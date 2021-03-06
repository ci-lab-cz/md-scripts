#!/usr/bin/env python3

import argparse
import MDAnalysis as mda
import prolif as plf


class RawTextArgumentDefaultsHelpFormatter(argparse.RawTextHelpFormatter, argparse.ArgumentDefaultsHelpFormatter):
    pass


def main():
    parser = argparse.ArgumentParser(description='Get protein-ligand interactions from MD trajectories using '
                                                 'ProLIF module.',
                                     formatter_class=RawTextArgumentDefaultsHelpFormatter)
    parser.add_argument('-i', '--trajectory', metavar='FILENAME', required=True,
                        help='input trajectory file (XTC).')
    parser.add_argument('-t', '--topology', metavar='FILENAME', required=True,
                        help='input topology file (TPR).')
    parser.add_argument('-l', '--ligand', metavar='STRING', required=False, default='UNL',
                        help='residue name of a ligand in the input trajectory.')
    parser.add_argument('-s', '--step', metavar='INTEGER', required=False, default=1, type=int,
                        help='step to take every n-th frame.')
    parser.add_argument('-a', '--append_protein_selection', metavar='STRING', required=False, default=None,
                        help='the string which will be concatenated to the protein selection atoms. '
                             'Example: "resname ZN or resname MG".')
    parser.add_argument('-o', '--output', metavar='FILENAME', required=True,
                        help='output text file name')
    parser.add_argument('-v', '--verbose', action='store_true', default=False,
                        help='print progress.')

    args = parser.parse_args()
    u = mda.Universe(args.topology, args.trajectory)
    lig = u.atoms.select_atoms(f'resname {args.ligand}')
    if args.append_protein_selection is None:
        protein_selection = 'protein'
    else:
        protein_selection = f'protein or {args.append_protein_selection}'
    prot = u.atoms.select_atoms(protein_selection)
    fp = plf.Fingerprint(['Hydrophobic', 'HBDonor', 'HBAcceptor', 'Anionic', 'Cationic', 'CationPi', 'PiCation',
                          'PiStacking', 'MetalAcceptor'])
    fp.run(u.trajectory[::args.step], lig, prot, progress=args.verbose)
    df = fp.to_dataframe()
    df.columns = ['.'.join(item.strip().lower() for item in items[1:]) for items in df.columns]
    df.to_csv(args.output, sep='\t')


if __name__ == '__main__':
    main()
