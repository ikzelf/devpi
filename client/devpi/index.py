from devpi.use import parse_keyvalue_spec

def index_create(hub, url, kvdict):
    hub.http_api("put", url, kvdict)
    index_show(hub, url)

def index_modify(hub, url, kvdict):
    indexconfig = get_indexconfig_reply(hub, url, ok404=False)
    for name, val in kvdict.items():
        indexconfig[name] = val
        hub.info("%s changing %s: %s" %(url.path, name, val))

    hub.http_api("patch", url, indexconfig)
    index_show(hub, url)

def index_delete(hub, url):
    hub.http_api("delete", url, None)
    hub.info("index deleted: %s" % url)

def index_list(hub, indexname):
    url = hub.current.get_user_url().asdir()
    res = hub.http_api("get", url, None)
    for name in res["result"]:
        hub.info(name)

def get_indexconfig_reply(hub, url, ok404=False):
    """ return 2-tuple of index url and indexconfig
    or None if configuration query failed. """
    res = hub.http_api("get", url, None, quiet=True)
    if res.status_code == 200:
        if res["type"] != "indexconfig":
            hub.fatal("%s: wrong result type: %s" % (url, res["type"]))
        return res["result"]
    elif res.status_code == 404 and ok404:
        return None
    hub.fatal("%s: trying to get json resulted in: %s %s"
                %(url.path, res.status_code, res.reason))

def index_show(hub, url):
    if not url:
        hub.fatal("no index specified and no index in use")
    ixconfig = get_indexconfig_reply(hub, url, ok404=False)
    hub.info(url.url + ":")
    hub.line("  type=%s" % ixconfig["type"])
    hub.line("  bases=%s" % ",".join(ixconfig["bases"]))
    hub.line("  volatile=%s" % (ixconfig["volatile"],))
    hub.line("  uploadtrigger_jenkins=%s" %(
                ixconfig["uploadtrigger_jenkins"],))
    hub.line("  acl_upload=%s" % ",".join(ixconfig["acl_upload"]))

def parse_posargs(hub, args):
    indexname = args.indexname
    keyvalues = list(args.keyvalues)
    if indexname and "=" in indexname:
        keyvalues.append(indexname)
        indexname = None
    kvdict = parse_keyvalue_spec_index(hub, keyvalues)
    return indexname, kvdict

def main(hub, args):
    indexname, kvdict = parse_posargs(hub, args)

    if args.list:
        return index_list(hub, indexname)

    url = hub.current.get_index_url(indexname, slash=False)

    if (args.delete or args.create) and not indexname:
        hub.fatal("need to explicitly specify index for deletion/creation")
    if args.delete:
        if args.keyvalues:
            hub.fatal("cannot delete if you specify key=values")
        return index_delete(hub, url)
    if args.create:
        return index_create(hub, url, kvdict)
    if kvdict:
        return index_modify(hub, url, kvdict)
    else:
        return index_show(hub, url)

def parse_keyvalue_spec_index(hub, keyvalues):
    try:
        kvdict = parse_keyvalue_spec(keyvalues)
    except ValueError:
        hub.fatal("arguments must be format NAME=VALUE: %r" %( keyvalues,))
    if "acl_upload" in kvdict:
        kvdict["acl_upload"] = kvdict["acl_upload"].split(",")
    if "bases" in kvdict:
        kvdict["bases"] = [x for x in kvdict["bases"].split(",") if x]
    return kvdict
