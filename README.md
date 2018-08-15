SwIPC
=====

Your one-stop-shop for Nintendo Switch IPC definitions.  This repo contains our best info on the state of IPC interfaces as of version 3.0, along with a parser in Python and scripts to generate and manipulate these files.

Layout
------

- `ipcdefs` -- The actual IPC definitions, in the various `.id` files.
- `scripts` -- Various scripts.  Some notable ones:
	- `genallipc.py` -- This is what generates `auto.id`.  That should be up to date in the repo, so you only need to run this when you're actively modifying the data in this script.
- `idparser.py` -- This is our module for parsing interface definitions from Python.

Syntax
------

### Types

These are the types that are permitted in SwIPC:
- `u8, u16, u32, u64` - Unsigned integers
- `i8, i16, i32, i64` - Signed integers
- `b8` - Boolean
- `f32` - Floating point
- `bytes<size[, alignment]>` - BLOB
- `unknown` - No semantic information nor any size information is available
- `unknown<size>` - No semantic information is available, but the size is known. This is equivalent to `bytes<size>`
- `data` - Untyped data, for use in `buffer<>` expressions
- `struct { type name; ... }` - Structured data
A type may be followed by a number in square brackets to represent that it is an array of that type with the given length.

### Decorators

Type definitions, interface definitions, and command definitions can all be decorated to provide additional information. They are placed before the definition, typically on their own line.

#### @version

Currently, the only specified decorator is the version decorator, which provides information about which versions the following definition applies to.

```
@version(2.0.0)
type nn::hid::debug::FirmwareVersion = i32;
```

Inside the parentheses is a version range, which can take the form of a single version (`1.0.0`, `2.0.0`, etc.), an inclusive range of versions (`1.0.0-3.0.0`), or a beginning version with no end (`2.0.0+`).

Multiple conflicting definitions can be made if they are decorated with different version ranges.

```
@version(1.0.0-3.0.0)
[200] OpenLibraryAppletProxy(u64, pid, KHandle<copy>) -> object<nn::am::service::ILibraryAppletProxy>;
@version(3.0.0+)
[200] OpenLibraryAppletProxyOld(u64, pid, KHandle<copy>) -> object<nn::am::service::ILibraryAppletProxy>;
```

### Typedefs

You can define a type using a `type` statement. Type statements can be decorated with `@version` decorators, and can conflict with each other as long as their versions do not overlap.
```
type nn::ApplicationId = i32;
type nn::account::CallbackUri = bytes<0x100>;
type nn::socket::timeout = struct {
	u64 sec;
	u64 usec;
	u64 off;
}; // note that there is a semicolon after the closing curly brace
type 
type nn::socket::sockaddr = unknown; // size is unknown
```

### Interface blocks

An `interface` block defines the list of commands on a given class. A `@version` decorator applied to an `interface` block means that the entire interface only exists on those versions.
```
interface nn::am::service::IAudioController {
	[0] SetExpectedMasterVolume(f32, f32);
	[1] GetMainAppletExpectedMasterVolume() -> f32;
	[2] GetLibraryAppletExpectedMasterVolume() -> f32;
	[3] ChangeMainAppletMasterVolume(f32, u64);
	[4] SetTransparentVolumeRate(f32);
}
```
If the interface represents a service registered with `sm:`, its registration can also be represented with an `is` clause.
```
interface nn::apm::IManager is apm {
	[0] OpenSession() -> object<nn::apm::ISession>;
	[1] GetPerformanceMode() -> nn::apm::PerformanceMode;
}
```
Multiple registrations for the same interface can also be represented.
```
interface nn::bcat::detail::ipc::IServiceCreator is bcat:a, bcat:m, bcat:u, bcat:s {
	[0] CreateBcatService(u64, pid) -> object<nn::bcat::detail::ipc::IBcatService>;
	[1] CreateDeliveryCacheStorageService(u64, pid) -> object<nn::bcat::detail::ipc::IDeliveryCacheStorageService>;
	[2] CreateDeliveryCacheStorageServiceWithApplicationId(nn::ApplicationId) -> object<nn::bcat::detail::ipc::IDeliveryCacheStorageService>;
}
```

Inside the `interface` block are command definitions. They should be indented with one tab character.

#### Command definitions

A command definition takes the following format.
```
[command id] Name(parameters) -> values;
```
If there are no values, everything between the closing paren and the semicolon can be omitted. If there is more than one, they need to be wrapped in a pair of parentheses and separated by commas.

Command definitions can be decorated with the `@version` decorator, and definitions can conflict as long as their versions do not overlap.

The parameters represent the fields and descriptors that need to be included in a request destined for this endpoint. Note that the request will also need to include any buffers or arrays defined in the `values` section.

The values, aside from any buffers or arrays, represent the values that will be included in a well-formed response from this endpoint.

In addition to any types built in or elsewhere defined, the parameters and values of a command can also include the following.
- `pid` - The message must include a handle descriptor with the "send PID" flag set
- `handle<move/copy/unknown>` - A handle included in the handle descriptor.
- `handle<move/copy/unknown, type>` - A handle representing the given type of kernel object.
- `buffer<data_type, transfer_type, size>` - A buffer that needs to be included in the request. `transfer_type` is the only field that is required to not be `unknown`. `size` may be a positive integer (matching the size of `data_type` if it is specified), `unknown` if the size is unknown, or `variable` if the size is known not to be checked. Translation between buffers of a given `transfer_type` and a set of A/B/C/X descriptors is [described on SwitchBrew](http://switchbrew.org/index.php?title=IPC_Marshalling#Official_marshalling_code).
- `buffer<data, transfer_type>` - A buffer transferring untyped data with variable size.
- `array<data_type, transfer_type>` - Equivalent to a buffer of the given `data_type` and `transfer_type` with a variable `size`.
- `object<interface_name/unknown>` - An object of the given type.

About auto.id and genallipc
---------------------------

genallipc.py is auto-generated from SDK symbols, which will in turn generate the `auto.id`. This will miss some symbols, because the SDK symbols are not necessarily complete.

From a conversation with @hthh :

What's with serverInfo and clientInfo ?

I have two scripts, one for "server" and one for "client".  "Server" does dynamic analysis of server code (using unicorn), which can reliably extract data from server dispatch functions. The fields available are inbytes, outbytes, ininterfaces, outinterfaces, inhandles, outhandles, buffers and sends_pid. But back when we did this we hadn't found a way to dump the builtin code, so we got docs with lots of information, but no information for FS or LDR or NCM which was annoying.

So "client" just works by extracting the command ID and sometimes the interface name from client code vtables. In the SDK it extracts the mangled symbols which sometimes includes the full method name and parameter types, and usually includes full parameter serialization information. So this is 2 mangled function names associated with a command ID. Unfortunately these are mostly fixed limitations. Much of the data has been compiled out and can't be recovered, particularly names and types. Serialization data can be recovered by hand, but I couldn't find a way to automate it.

2.0 was the first version to include the 2nd mangled function name, so we get 1.0 types/names but not serialization data. Interface names were removed from the serverside data available on 4.1, so I wrote a dynamic client script which can figure out the input buffer types and (rough) input data size using unicorn and used that to match things. This is also interesting for things like TMA services where we only have client code and no server code.

I should really write this all up in a better format sometime. Basically I've done my best to extract this data, but I haven't addressed the huge problem of turning it into something coherent and useful.
