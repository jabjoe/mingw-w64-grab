#! /usr/bin/python3
import os
from bs4 import BeautifulSoup
from dateutil import parser
from tqdm import tqdm
import requests
import math
import sys

target = os.environ["MINGW_TARGET"] if "MINGW_TARGET" in os.environ else 'i686'

platform = 'mingw-w64-%s' % target

working_dir = "/tmp"

url = 'http://repo.msys2.org/mingw/%s/' % target
ext = 'xz'


def get_pkg_links(url, ext=''):
    page = requests.get(url).text
    soup = BeautifulSoup(page, 'html.parser')
    raw = [(url + '/' + node.get('href'), parser.parse(node.next_sibling.strip(" ").split("   ")[0])) for node in soup.find_all('a') if node.get('href').endswith(ext)]
    t = {}
    for i in raw:
        parts = i[0].split("/")[-1].replace("%s-" % platform,"").split("-")
        name = '%s-%s' % (platform, "-".join(parts[:-3]))
        if not name in t:
            t[name] = {i[1] : i[0]}
        else:
            t[name][i[1]] = i[0]
    r = {}
    for name in t:
        entry = t[name]
        keys = list(entry.keys())
        keys.sort()
        r[name] = entry[keys[-1]]
    return r


def download_pkg(name, pkgs):
    pkg_url = pkgs[name]
    filename = working_dir + "/" + pkg_url.split("/")[-1]
    if os.path.exists(filename):
        return filename, True
    response = requests.get(pkg_url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    block_size = 1024
    wrote = 0 
    print("Downloading : %s" % filename)
    with open(filename, "wb") as f:
        for data in tqdm(response.iter_content(block_size), total=math.ceil(total_size//block_size) , unit='KB', unit_scale=True):
                wrote = wrote  + len(data)
                f.write(data)
    return filename, False


def extract_pkg(filename):
    cmd = 'tar xf "%s" -C "%s"' % (filename, working_dir)
    r = os.system(cmd)
    assert r == 0


def find_dependencies():
    pkginfo = "%s/.PKGINFO" % working_dir
    r = []
    with open(pkginfo) as f:
        for line in f:
            if line.startswith("depend ="):
                r += [line.split("=")[1].strip().split(">")[0]]
    print("Require :", r)
    return r



def install(package):
    print("Installing : %s" % package)
    if not package in pkgs:
        git_package = package + "-git"
        if not git_package in pkgs:
            print('Unable to find "%s", skipping' % package)
            return
        package = git_package
    filename, done = download_pkg(package, pkgs)

    if done:
        return

    extract_pkg(filename)

    deps = find_dependencies()

    for dep in deps:
        install(dep)



pkgs = get_pkg_links(url, ext)



def list_pkgs():
    for pkg in pkgs:
        print(pkg, pkgs[pkg])


if len(sys.argv) < 2:
    print("Please give command : list or install <package>")
    print("Environment Variable MINGW_TARGET for i686 or x86_64")
    sys.exit(-1)

cmds = {"list": list_pkgs, "install" : lambda : install(sys.argv[2])}

cmd = sys.argv[1]

if cmd not in cmds:
    print("Unknown command : %s" % cmd)
    sys.exit(-1)

cmds[cmd]()






