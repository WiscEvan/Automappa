#!/usr/bin/env python


import os
import glob

from autometa.common.external import hmmscan
from celery import Celery, chain

app = Celery("tasks", broker="pyamqp://guest@localhost//")


@app.task
def hmmdb_formatter(hmmdb) -> None:
    hmmscan.hmmpress(hmmdb)


@app.task
def scanner(seqfile, hmmdb, out) -> str:
    # NOTE: returns outfpath
    # cmd = [
    #     "hmmscan",
    #     "--cpu",
    #     "1",
    #     "--seed",
    #     "42",
    #     "--tblout",
    #     out,
    #     hmmdb,
    #     seqfile
    # ]
    # run_cmd = " ".join(cmd)
    # os.system(run_cmd)
    hmmscan.run(
        orfs=seqfile,
        hmmdb=hmmdb,
        outfpath=out,
        cpus=2,
        parallel=True,
        seed=42,
        force=True,
    )


if __name__ == "__main__":
    hmmdb_dir = "/Users/rees/Wisc/kwan/for_brian/complex_metagenomes/marker_annotater/test_data/hmms"
    orfs_dir = "/Users/rees/Wisc/kwan/for_brian/complex_metagenomes/marker_annotater/test_data/orfs"
    outdir = "/Users/rees/Wisc/kwan/for_brian/complex_metagenomes/marker_annotater/test_data/hmmscan"
    if not os.path.exists(outdir) or not os.path.isdir(outdir):
        os.makedirs(outdir)
    for seqfile in glob.glob(os.path.join(orfs_dir, "*.orfs.faa")):
        hmmdb_filename = os.path.basename(seqfile).replace(".orfs.faa", ".hmm")
        hmmdb = os.path.join(hmmdb_dir, hmmdb_filename)
        if not os.path.exists(hmmdb):
            continue
        outfilename = os.path.basename(seqfile).replace(".faa", ".hmmscan.tsv")
        out = os.path.join(outdir, outfilename)
        hmmdb_formatter.s(hmmdb).apply_async()
        scanner.s(seqfile, hmmdb, out).apply_async(countdown=2)
