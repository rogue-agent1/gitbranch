#!/usr/bin/env python3
"""gitbranch - Git branch management helper."""
import subprocess, argparse, sys, re

def git(*args):
    r = subprocess.run(['git'] + list(args), capture_output=True, text=True)
    return r.stdout.strip(), r.returncode

def main():
    p = argparse.ArgumentParser(description='Git branch helper')
    sub = p.add_subparsers(dest='cmd')
    
    ls = sub.add_parser('list', help='List branches with details')
    ls.add_argument('-a', '--all', action='store_true')
    ls.add_argument('-r', '--remote', action='store_true')
    ls.add_argument('--merged', action='store_true')
    ls.add_argument('--no-merged', action='store_true')
    
    cl = sub.add_parser('clean', help='Delete merged branches')
    cl.add_argument('--dry-run', action='store_true')
    cl.add_argument('--base', default='main', help='Base branch')
    
    ag = sub.add_parser('age', help='Show branch ages')
    ag.add_argument('-n', type=int, default=20)
    
    sz = sub.add_parser('ahead', help='Show ahead/behind counts')
    sz.add_argument('--base', default='main')
    
    args = p.parse_args()
    if not args.cmd: args.cmd = 'list'; args.all = False; args.remote = False; args.merged = False; args.no_merged = False
    
    if args.cmd == 'list':
        flags = []
        if args.all: flags.append('-a')
        elif args.remote: flags.append('-r')
        if args.merged: flags.append('--merged')
        if args.no_merged: flags.append('--no-merged')
        
        out, _ = git('branch', '-v', '--sort=-committerdate', *flags)
        current, _ = git('rev-parse', '--abbrev-ref', 'HEAD')
        for line in out.split('\n'):
            if not line.strip(): continue
            is_current = line.startswith('*')
            marker = '→' if is_current else ' '
            print(f"{marker} {line.strip()}")
    
    elif args.cmd == 'clean':
        merged, _ = git('branch', '--merged', args.base)
        branches = [b.strip() for b in merged.split('\n') if b.strip() and not b.strip().startswith('*') and b.strip() not in ('main','master','develop')]
        if not branches:
            print("No merged branches to clean."); return
        for b in branches:
            if args.dry_run:
                print(f"  Would delete: {b}")
            else:
                git('branch', '-d', b)
                print(f"  Deleted: {b}")
        print(f"\n{'Would delete' if args.dry_run else 'Deleted'} {len(branches)} branches")
    
    elif args.cmd == 'age':
        out, _ = git('for-each-ref', '--sort=-committerdate', '--format=%(refname:short) %(committerdate:relative) %(authorname)',
                      'refs/heads/')
        for i, line in enumerate(out.split('\n')[:args.n]):
            if line.strip():
                parts = line.split(' ', 1)
                print(f"  {parts[0]:<30} {parts[1]}")
    
    elif args.cmd == 'ahead':
        branches, _ = git('for-each-ref', '--format=%(refname:short)', 'refs/heads/')
        for branch in branches.split('\n'):
            if not branch.strip(): continue
            counts, _ = git('rev-list', '--left-right', '--count', f'{args.base}...{branch}')
            if counts:
                behind, ahead = counts.split('\t')
                if int(ahead) > 0 or int(behind) > 0:
                    print(f"  {branch:<30} +{ahead} -{behind}")

if __name__ == '__main__':
    main()
