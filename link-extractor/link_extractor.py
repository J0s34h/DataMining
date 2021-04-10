import requests
import colorama
import sys
import threading

import time

import random
from concurrent.futures.thread import ThreadPoolExecutor

from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

import treelib
from treelib import Tree

import graphviz
from graphviz import Digraph, Source

import pprint

tree = Tree()
main_graph = Digraph()
main_graph.clear()

# init the colorama module
colorama.init()

GREEN = colorama.Fore.GREEN
GRAY = colorama.Fore.LIGHTBLACK_EX
RESET = colorama.Fore.RESET

# initialize the set of links (unique links)
internal_urls = set()
external_urls = set()

total_urls_visited = 0


def is_valid(url):
    """
    Checks whether `url` is a valid URL.
    """
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)


def get_all_website_links(url, parent_url=""):
    """
    Returns all URLs that is found on `url` in which it belongs to the same website
    """
    # all URLs of `url`
    urls = set()
    # domain name of the URL without the protocol
    domain_name = urlparse(url).netloc
    try:
        soup = BeautifulSoup(requests.get(url, timeout=1).content, "html.parser", )
    except requests.exceptions.InvalidSchema:
        return urls
    except requests.exceptions.ConnectionError:
        return urls
    except:
        return urls

    for a_tag in soup.findAll("a"):
        href = a_tag.attrs.get("href")
        if href == "" or href is None:
            # href empty tag
            continue
        # join the URL if it's relative (not absolute link)
        href = urljoin(url, href)
        parsed_href = urlparse(href)
        # remove URL GET parameters, URL fragments, etc.
        href = parsed_href.scheme + "://" + parsed_href.netloc + parsed_href.path
        if not is_valid(href):
            # not a valid URL
            continue
        if href in internal_urls:
            # already in the set
            continue
        if domain_name not in href:
            # external link
            if href not in external_urls:
                print(f"{GRAY}[!] External link: {href}{RESET}")
                add_node(href, parent_url, is_external=True)
                urls.add(href)
                external_urls.add(href)
            continue
        print(f"{GREEN}[*] Internal link: {href}{RESET}")
        add_node(href, parent_url, is_external=False)
        urls.add(href)
        internal_urls.add(href)
    return urls


def crawl(url, max_depth=1, depth=1, parent_url="Parent url", total_urls_seen=0):
    """
    Crawls a web page and extracts all links.
    You'll find all links in `external_urls` and `internal_urls` global set variables.
    params:
        max_urls (int): number of max urls to crawl, default is 30.
    """

    links = get_all_website_links(url, parent_url=url)

    # with ThreadPoolExecutor() as executor:
    #     for link in links:
    #         total_urls_seen += 1
    #         if depth == max_depth:
    #             print(f"Thread has reached required depth {total_urls_seen}")
    #             break
    #         elif total_urls_seen > 1000:
    #             print("Thread has seen enough")
    #             break
    #         executor.submit(crawl, url=link, depth=depth + 1, max_depth=max_depth, parent_url=link,
    #                         total_urls_seen=total_urls_seen)

    for link in links:
        total_urls_seen += 1
        if depth == max_depth:
            print(f"Thread has reached required depth {total_urls_seen}")
            break
        elif total_urls_seen > 1000:
            print("Thread has seen enough")
            break
        threading.Thread(target=crawl, args=(link, max_depth, depth + 1, link, total_urls_seen)).start()
        # crawl(link, depth=depth + 1, parentUrl=link)


def remove_protocol(url):
    return url.replace(":", "")


def add_node(childUrl, parentUrl, is_external=True):
    try:
        if is_external:
            if not external_urls.__contains__(childUrl):
                main_graph.node(remove_protocol(childUrl), remove_protocol(childUrl), color="red")
            # if not external_urls.__contains__(parentUrl):
            #     main_graph.node(remove_protocol(parentUrl), remove_protocol(parentUrl), color="red")
        else:
            if not internal_urls.__contains__(childUrl):
                main_graph.node(remove_protocol(childUrl), remove_protocol(childUrl), color="blue")
            # if not internal_urls.__contains__(parentUrl):
            #     main_graph.node(remove_protocol(parentUrl), remove_protocol(parentUrl), color="blue")

        main_graph.edge(remove_protocol(parentUrl), remove_protocol(childUrl))
        tree.create_node(childUrl, childUrl, parent=parentUrl)
    except treelib.exceptions.DuplicatedNodeIdError:
        print(f"Dupicate ID error for parent {parentUrl} with child {childUrl}")


if __name__ == "__main__":
    import argparse

    print(f"{GREEN} Max depth limit: {sys.getrecursionlimit()}{RESET}")
    sys.setrecursionlimit(12_000)

    parser = argparse.ArgumentParser(description="Link Extractor Tool with Python")
    parser.add_argument("url", help="The URL to extract links from.")
    parser.add_argument("-m", "--max-urls", help="Number of max URLs to crawl, default is 30.", default=30, type=int)
    parser.add_argument("-d", "--depth", help="Target depth of", default=1, type=int)

    args = parser.parse_args()
    url = args.url
    max_urls = args.max_urls
    max_depth = args.depth

    tree.create_node(url, url)  # root
    external_urls.add(url)
    main_graph.node(url, "ROOT")

    crawl(url, parent_url=url, max_depth=max_depth)

    while True:
        if threading.activeCount() > 1:
            print(f"THREADS RUNNING " + str(threading.activeCount()))
            time.sleep(3)
            continue

        print("[+] Total Internal links:", len(internal_urls))
        print("[+] Total External links:", len(external_urls))
        print("[+] Total URLs:", len(external_urls) + len(internal_urls))

        domain_name = urlparse(url).netloc

        # save the internal links to a file
        with open(f"{domain_name}_internal_links.txt", "w") as f:
            for internal_link in internal_urls:
                print(internal_link.strip(), file=f)

        # save the external links to a file
        with open(f"{domain_name}_external_links.txt", "w") as f:
            for external_link in external_urls:
                print(external_link.strip(), file=f)

        tree.save2file('tree.txt')
        tree.to_graphviz("graph.gv")

        # text_from_file = str()
        # with open('graph') as file:
        #     text_from_file = file.read()
        #
        # src = Source(text_from_file)
        # src.filename = "GraphvizOutput.gv"
        # src.render(view=True)

        main_graph.render()

        tree.show()

        break
