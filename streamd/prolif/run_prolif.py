#!/usr/bin/env python3

import argparse
import os
import shutil
from functools import partial
from glob import glob
from multiprocessing import cpu_count

import MDAnalysis as mda
import pandas as pd
import prolif as plf

from streamd.utils.dask_init import init_dask_cluster, calc_dask
from streamd.utils.utils import filepath_type


class RawTextArgumentDefaultsHelpFormatter(argparse.RawTextHelpFormatter, argparse.ArgumentDefaultsHelpFormatter):
    pass


def backup_output(output):
    if os.path.isfile(output):
        all_outputs = glob(os.path.join(os.path.dirname(output), f'#{os.path.basename(output)}*#'))
        n = len(all_outputs) + 1
        shutil.move(output, os.path.join(os.path.dirname(output), f'#{os.path.basename(output)}.{n}#'))


def run_prolif_task(tpr, xtc, protein_selection, ligand_selection, step, verbose, output, n_jobs):
    u = mda.Universe(tpr, xtc)

    protein = u.atoms.select_atoms(protein_selection)
    ligand = u.atoms.select_atoms(ligand_selection)

    fp = plf.Fingerprint(['Hydrophobic', 'HBDonor', 'HBAcceptor', 'Anionic', 'Cationic', 'CationPi', 'PiCation',
                          'PiStacking', 'MetalAcceptor'])
    fp.run(u.trajectory[::step], ligand, protein, progress=verbose, n_jobs=n_jobs)
    df = fp.to_dataframe()
    df.columns = ['.'.join(item.strip().lower() for item in items[1:]) for items in df.columns]
    df = df.reindex(sorted(df.columns), axis=1)
    df.to_csv(output, sep='\t')
    return df


def run_prolif_from_wdir(wdir, tpr, xtc, protein_selection, ligand_selection, step, verbose, output, n_jobs):
    tpr = os.path.join(wdir, tpr)
    xtc = os.path.join(wdir, xtc)
    output = os.path.join(wdir, output)
    backup_output(output)

    if not os.path.isfile(tpr) or not os.path.isfile(xtc):
        print(f'{wdir}: cannot run gbsa. Check if there are missing files: {tpr} {xtc}. Skip such directory')
        return None

    run_prolif_task(tpr, xtc, protein_selection, ligand_selection, step, verbose, output, n_jobs)
    return output


def collect_outputs(output_list, output):
    df_list = []
    for i in output_list:
        df = pd.read_csv(i, sep='\t')
        df['fname'] = i
        df_list.append(df)

    df_aggregated = pd.concat(df_list)
    df_aggregated = df_aggregated.fillna(False).sort_values('Frame')
    amino_acids = df_aggregated.columns.drop(['fname', 'Frame']).to_list()
    # sort by number and type of interaction
    amino_acids.sort(key=lambda x: (int(x.split('.')[0][3:]), x.split('.')[1]))
    sorted_columns = ['fname', 'Frame'] + amino_acids
    df_aggregated.loc[:, sorted_columns].to_csv(output, sep='\t', index=False)


def start(wdir_to_run, wdir_output, tpr, xtc, step, append_protein_selection, ligand_resid, hostfile, ncpu, verbose):
    output = 'plifs.csv'
    output_aggregated = os.path.join(wdir_output, 'prolif_output.csv')

    # problem with n_jobs
    # if hostfile:
    #     with open(hostfile) as f:
    #         hosts = [line.strip() for line in f if line.strip()]
    #         n_servers = len(hosts)
    # else:
    #     n_servers = 1

    if append_protein_selection is None:
        protein_selection = 'protein'
    else:
        protein_selection = f'protein or {append_protein_selection}'

    ligand_selection = f'resname {ligand_resid}'

    if wdir_to_run is not None:
        dask_client, cluster = None, None
        # n_tasks_per_node = min(math.ceil(len(wdir_to_run) / n_servers), ncpu)
        n_tasks_per_node = min(len(wdir_to_run), ncpu)
        njobs_per_task = 1
        # njobs_per_task = math.floor(ncpu / n_tasks_per_node)
        try:
            dask_client, cluster = init_dask_cluster(hostfile=hostfile, n_tasks_per_node=n_tasks_per_node, ncpu=ncpu)
            var_prolif_out_files = []
            for res in calc_dask(run_prolif_from_wdir, wdir_to_run, dask_client=dask_client,
                                 tpr=tpr, xtc=xtc, protein_selection=protein_selection,
                                 ligand_selection=ligand_selection, step=step, verbose=verbose, output=output,
                                 n_jobs=njobs_per_task):
                if res:
                    var_prolif_out_files.append(res)
        finally:
            if dask_client:
                dask_client.retire_workers(dask_client.scheduler_info()['workers'], on_error='ignore',
                                           close_workers=True, remove=True)
                dask_client.shutdown()
            if cluster:
                cluster.close()
    else:
        output = os.path.join(os.path.dirname(xtc), output)
        run_prolif_task(tpr, xtc, protein_selection, ligand_selection, step, verbose, output, n_jobs=ncpu)
        var_prolif_out_files = [output]

    backup_output(output_aggregated)
    collect_outputs(var_prolif_out_files, output=output_aggregated)


def main():
    parser = argparse.ArgumentParser(description='Get protein-ligand interactions from MD trajectories using '
                                                 'ProLIF module.',
                                     formatter_class=RawTextArgumentDefaultsHelpFormatter)
    parser.add_argument('-i', '--wdir_to_run', metavar='DIRNAME', required=False, default=None, nargs='+',
                        type=partial(filepath_type, exist_type='dir'),
                        help='''single or multiple directories for simulations.
                             Should consist of: md_out.tpr and md_fit.xtc files''')
    parser.add_argument('--xtc', metavar='FILENAME', required=False,
                        help='input trajectory file (XTC). Will be ignored if --wdir_to_run is used')
    parser.add_argument('--tpr', metavar='FILENAME', required=False,
                        help='input topology file (TPR). Will be ignored if --wdir_to_run is used')
    parser.add_argument('-l', '--ligand', metavar='STRING', required=False, default='UNL',
                        help='residue name of a ligand in the input trajectory.')
    parser.add_argument('-s', '--step', metavar='INTEGER', required=False, default=1, type=int,
                        help='step to take every n-th frame. ps')
    parser.add_argument('-a', '--append_protein_selection', metavar='STRING', required=False, default=None,
                        help='the string which will be concatenated to the protein selection atoms. '
                             'Example: "resname ZN or resname MG".')
    parser.add_argument('-d', '--wdir', metavar='WDIR', default=None,
                        type=partial(filepath_type, check_exist=False, create_dir=True),
                        help='Working directory for program output. If not set the current directory will be used.')
    parser.add_argument('-v', '--verbose', action='store_true', default=False,
                        help='print progress.')
    parser.add_argument('--hostfile', metavar='FILENAME', required=False, type=str, default=None,
                        help='text file with addresses of nodes of dask SSH cluster. The most typical, it can be '
                             'passed as $PBS_NODEFILE variable from inside a PBS script. The first line in this file '
                             'will be the address of the scheduler running on the standard port 8786. If omitted, '
                             'calculations will run on a single machine as usual.')
    parser.add_argument('-c', '--ncpu', metavar='INTEGER', required=False, default=cpu_count(), type=int,
                        help='number of CPU per server. Use all cpus by default.')

    args = parser.parse_args()

    if args.wdir is None:
        wdir = os.getcwd()
    else:
        wdir = args.wdir

    if args.wdir_to_run is not None:
        tpr = 'md_out.tpr'
        xtc = 'md_fit.xtc'
    else:
        tpr = args.tpr
        xtc = args.xtc

    start(wdir_to_run=args.wdir_to_run, wdir_output=wdir, tpr=tpr,
          xtc=xtc, step=args.step, append_protein_selection=args.append_protein_selection,
          ligand_resid=args.ligand, hostfile=args.hostfile, ncpu=args.ncpu, verbose=args.verbose)


if __name__ == '__main__':
    main()
