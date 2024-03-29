import logging
import math
import os

from dask.distributed import Client, SSHCluster
from rdkit import Chem

def set_env(main_os_env):
    os.environ["PATH"] = f'{main_os_env["PATH"]}:{os.environ["PATH"]}'
    os.environ["CONDA_DEFAULT_ENV"] = main_os_env["CONDA_DEFAULT_ENV"]
    os.environ["CONDA_PREFIX"] = main_os_env["CONDA_PREFIX"]
    os.environ["CONDA_PROMPT_MODIFIER"] = main_os_env["CONDA_PROMPT_MODIFIER"]
    os.environ["CONDA_SHLVL"] = main_os_env["CONDA_SHLVL"]


def init_dask_cluster(n_tasks_per_node, ncpu, hostfile=None):
    '''

    :param n_tasks_per_node: number of task on a single server
    :param ncpu: number of cpu on a single server
    :param hostfile:
    :return:
    '''
    if hostfile:
        with open(hostfile) as f:
            hosts = [line.strip() for line in f if line.strip()]
            n_servers = len(hosts)
    else:
        hosts = []
        n_servers = 1

    # n_workers = n_servers * n_tasks_per_node
    n_workers = n_tasks_per_node
    n_threads = math.ceil(ncpu / n_tasks_per_node)
    if hostfile is not None:
        logging.warning(f'Dask init,{n_tasks_per_node}, {ncpu}, {n_threads}, {n_workers}, {hosts},{n_servers}')
        cluster = SSHCluster(
            [hosts[0]] + hosts,
            connect_options={"known_hosts": None},
            worker_options={"nthreads": n_threads, 'n_workers': n_workers},
            scheduler_options={"port": 0, "dashboard_address": ":8786"},
        )
        dask_client = Client(cluster)

    else:
        cluster = None
        dask_client = Client(n_workers=n_workers, threads_per_worker=n_threads)  # to run dask on a single server

    dask_client.forward_logging(level=logging.INFO)
    dask_client.run(set_env, main_os_env=os.environ.copy())
    return dask_client, cluster


def calc_dask(func, main_arg, dask_client, dask_report_fname=None, **kwargs):
    main_arg = iter(main_arg)
    Chem.SetDefaultPickleProperties(Chem.PropertyPickleOptions.AllProps)
    if dask_client is not None:
        from dask.distributed import as_completed, performance_report
        # https://stackoverflow.com/a/12168252/895544 - optional context manager
        from contextlib import contextmanager
        none_context = contextmanager(lambda: iter([None]))()
        with (performance_report(filename=dask_report_fname) if dask_report_fname is not None else none_context):
            nworkers = len(dask_client.scheduler_info()['workers'])
            # logging.warning(f'dask {func}, {dask_client.scheduler_info()}, {nworkers}')
            futures = []
            for i, arg in enumerate(main_arg, 1):
                futures.append(dask_client.submit(func, arg, **kwargs))
                if i == nworkers:
                    break
            seq = as_completed(futures, with_results=True)
            for i, (future, results) in enumerate(seq, 1):
                yield results
                del future
                try:
                    arg = next(main_arg)
                    new_future = dask_client.submit(func, arg, **kwargs)
                    seq.add(new_future)
                except StopIteration:
                    continue
