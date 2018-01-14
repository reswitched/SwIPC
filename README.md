SwIPC
=====

Your one-stop-shop for Nintendo Switch IPC definitions.  This repo contains our best info on the state of IPC interfaces as of version 3.0, along with a parser in Python and scripts to generate and manipulate these files.

Layout
------

- `ipcdefs` -- The actual IPC definitions, in the various `.id` files.
- `scripts` -- Various scripts.  Some notable ones:
	- `genallipc.py` -- This is what generates `auto.id`.  That should be up to date in the repo, so you only need to run this when you're actively modifying the data in this script.
- `idparser.py` -- This is our module for parsing interface definitions from Python.

About auto.id and genallipc
---------------------------

genallipc.py is auto-generated from SDK symbols, which will in turn generate the `auto.id`. This will miss some symbols, because the SDK symbols are not necessarily complete.

From a conversation with @hthh :

What's with serverInfo and clientInfo ?

I have two scripts, one for "server" and one for "client".  "Server" does dynamic analysis of server code (using unicorn), which can reliably extract data from server dispatch functions. The fields available are inbytes, outbytes, ininterfaces, outinterfaces, inhandles, outhandles, buffers and sends_pid. But back when we did this we hadn't found a way to dump the builtin code, so we got docs with lots of information, but no information for FS or LDR or NCM which was annoying.

So "client" just works by extracting the command ID and sometimes the interface name from client code vtables. In the SDK it extracts the mangled symbols which sometimes includes the full method name and parameter types, and usually includes full parameter serialization information. So this is 2 mangled function names associated with a command ID. Unfortunately these are mostly fixed limitations. Much of the data has been compiled out and can't be recovered, particularly names and types. Serialization data can be recovered by hand, but I couldn't find a way to automate it.

2.0 was the first version to include the 2nd mangled function name, so we get 1.0 types/names but not serialization data. Interface names were removed from the serverside data available on 4.1, so I wrote a dynamic client script which can figure out the input buffer types and (rough) input data size using unicorn and used that to match things. This is also interesting for things like TMA services where we only have client code and no server code.

I should really write this all up in a better format sometime. Basically I've done my best to extract this data, but I haven't addressed the huge problem of turning it into something coherent and useful.
