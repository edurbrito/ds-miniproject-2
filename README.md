# ds-miniproject-2

-------------------

### Instructions (Tested in Linux)

Ensure you have Python installed.

Then, run the following command:

```
general-byzantine-problem.sh <N>
            N   number of processes (N > 0)
```

It will automatically create a virtual environment (`env` folder), if it does not exist, and install the requirements.
Finally it will start the algorithm by creating the N processes.

### Notes
 
Each node represents a general, running as an isolated process, child of the main process. 
Each process has a main thread which is bound to a socket exposing a multithreaded RPC service for handling concurrent connections.

Each process is listening on a port in the range [18812, 18812 + N]. Check `./ds-miniproject-2/env.py` for the default configuration values.

### Deliverables

###### `ds-miniproject-2` folder (aka `src` folder)

Contains all the source code, classes and configuration variables needed to run the program. The `__main__.py` file is the entrypoint for the program, which then just needs to be called with `python ./ds-miniproject-2 N`.

###### `docs` folder

Contains the specification PDF, and the video of a running example.

### Author

* Eduardo Ribas Brito
