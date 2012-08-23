#!/usr/bin/env python3

import argparse
import os.path
import os
import subprocess

def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('branch', help='The git branch name')
    arg_parser.add_argument('--repo-dir',
        default=os.path.join('..', 'bytestag.git'),
        help='The directory of the repo to switch to')

    args = arg_parser.parse_args()

    bzr_proc = subprocess.Popen(['bzr', 'fast-export', os.getcwd(),
        '--git-branch', args.branch],
        cwd=args.repo_dir, stdout=subprocess.PIPE,
    )
    git_proc = subprocess.Popen(['git', 'fast-import',],
        cwd=args.repo_dir, stdin=bzr_proc.stdout,
    )

    bzr_proc.stdout.close()
    git_proc.communicate()

    bzr_proc.wait()
    git_proc.wait()

if __name__ == '__main__':
    main()
