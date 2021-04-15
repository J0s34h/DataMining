import requests
import colorama
import sys
import threading

import time

from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

from fractions import Fraction

import treelib
from treelib import Tree
from graphviz import Digraph

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

node_connections = dict()

threads = [threading.Thread]


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
            add_node(href, parent_url, is_external=True)
            continue
        if domain_name not in href:
            # external link
            add_node(href, parent_url, is_external=True)

            if href not in external_urls:
                print(f"{GRAY}[!] External link: {href}{RESET}")
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
        elif total_urls_seen > max_urls:
            print("Thread has seen enough")
            break
        # Process(target=crawl, args=(link, max_depth, depth + 1, link, total_urls_seen)).start()
        thread = threading.Thread(target=crawl, args=(link, max_depth, depth + 1, link, total_urls_seen))

        thread.start()

        # crawl(link, max_depth, depth + 1, link, total_urls_seen)
    return

    # crawl(link, depth=depth + 1, parentUrl=link)


def remove_protocol(url):
    if url[len(url) - 1] == "/":
        url = url[:-1]

    return url.replace(":", "")


def add_node(childUrl, parentUrl, is_external=True):
    try:
        childUrl = remove_protocol(childUrl)
        parentUrl = remove_protocol(parentUrl)

        if node_connections.__contains__(parentUrl):
            node_connections.get(parentUrl).add(childUrl)
        else:
            node_connections.__setitem__(parentUrl, set(childUrl))

        # if is_external:
        #     if not external_urls.__contains__(childUrl):
        #         main_graph.node(remove_protocol(childUrl), remove_protocol(childUrl), color="red")
        #     # if not external_urls.__contains__(parentUrl):
        #     #     main_graph.node(remove_protocol(parentUrl), remove_protocol(parentUrl), color="red")
        # else:
        #     if not internal_urls.__contains__(childUrl):
        #         main_graph.node(remove_protocol(childUrl), remove_protocol(childUrl), color="blue")
        #     # if not internal_urls.__contains__(parentUrl):
        #     #     main_graph.node(remove_protocol(parentUrl), remove_protocol(parentUrl), color="blue")

        tree.create_node(childUrl, childUrl, parent=parentUrl)
    except treelib.exceptions.DuplicatedNodeIdError:
        # DO NOTHING, convenience tree can't handle duplicate leaves
        return


def transpon(matrix):
    return [[matrix[j][i] for j in range(len(matrix))] for i in range(len(matrix[0]))]


def page_rank_calcualtor(vector, matrix):
    old_vector = vector
    new_vector = vector
    print(old_vector)
    for i in range(1000):
        vector_index = 0
        for matrix_row in matrix:
            multiplication_sum = Fraction(0)
            index = 0
            for number in matrix_row:
                multiplication_sum = multiplication_sum.__add__(
                    old_vector[index].__mul__(number))
                index += 1
            new_vector[vector_index] = Fraction(multiplication_sum)
            vector_index += 1
        for value in new_vector:
            value.__mul__(Fraction(8, 10))
            value.__add__(Fraction(2, 10).__divmod__(Fraction(len(new_vector), 1)))
        old_vector = new_vector
        print(sum(new_vector).numerator / sum(new_vector).denominator)

    return new_vector


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

    tree.create_node(remove_protocol(url), remove_protocol(url))  # root

    internal_urls.add(url)
    crawl(url, parent_url=url, max_depth=max_depth)
    lastLength = -1
    while True:
        if threading.activeCount() <= 2:
            break
        elif threading.activeCount() == lastLength:
            break
        lastLength = threading.activeCount()
        time.sleep(30)

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

    tree.show()

    all_urls_set = set()
    all_urls_set.update(external_urls)
    all_urls_set.update(internal_urls)

    all_urls = list(all_urls_set)

    white_list = set(node_connections.keys())

    filtered_node_connection = dict()

    redo = True
    trusted_url = set()
    while redo:
        redo = False
        for k, v in node_connections.items():
            if not white_list.__contains__(k):
                continue

            result_set = set()
            for link in v:
                if white_list.__contains__(link) and link != k:
                    trusted_url.add(link)
                    result_set.add(link)

            if len(result_set) == 0:
                trusted_url.remove(k)
                white_list.remove(k)
                redo = True
                continue

            # if len(result_set) == 1:
            #     if not trusted_url.__contains__(k):
            #         white_list.remove(k)
            #         redo = True
            #         continue

            if len(result_set) > 0:
                filtered_node_connection.__setitem__(k, result_set)

        node_connections = filtered_node_connection

    for link in white_list:
        if link == remove_protocol(url):
            main_graph.node(remove_protocol(link), color="violet")
            continue

        if external_urls.__contains__(link):
            main_graph.node(remove_protocol(link), color="red")
        else:
            main_graph.node(remove_protocol(link), color="blue")

    for k, v in filtered_node_connection.items():
        for connectedTo in v:
            main_graph.edge(remove_protocol(k), remove_protocol(connectedTo))

    matrix = [[0 for x in range(0, len(white_list))] for y in range(0, len(white_list))]

    all_urls = list(white_list)

    if len(white_list) > 0:

        for k, v in node_connections.items():
            if not all_urls.__contains__(k):
                continue
            parentIndex = all_urls.index(k)
            divider_factor = len(v)
            for connectedTo in v:
                childIndex = all_urls.index(connectedTo)
                matrix[parentIndex][childIndex] = Fraction(1, len(v))

        for row in matrix:
            print(row)

        print("\n")

        matrix = transpon(matrix)

        for row in matrix:
            print(row)

        page_rank_vector = page_rank_calcualtor(vector=[Fraction(1, len(white_list)) for j in range(len(white_list))],
                                                matrix=matrix)
        page_rank_dict = dict()

        for idx in range(len(page_rank_vector)):
            page_rank_dict.__setitem__(list(white_list)[idx], page_rank_vector[idx])

        print(f"{page_rank_dict} \n")
        print(sum(page_rank_vector))

        main_graph.render(filename="TEST.gv")
        main_graph.view()
    else:
        print("EMPTY MATRIX")
