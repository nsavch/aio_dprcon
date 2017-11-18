aio-dprcon
==========

TEST A library and console client for DarkPlaces RCON protocol

Installation
------------

.. code:: bash

    $ pip install aio-dprcon

To use the console tool on windows please also install pyreadline

.. code:: bash

    $ pip install pyreadline

Note, that windows cmd doesn't support ANSI color codes. You can use
`MinTTY <https://mintty.github.io/>`__ instead

Console tool usage
------------------

.. code:: bash

    $ dprcon add  # Add a server
    $ dprcon refresh SERVER_NAME  # Fill completion cache (optional)
    $ dprcon connect SERVER_NAME  # Launch interactive RCON shell 

Or watch an ascii cast here - https://asciinema.org/a/148143

Library API
-----------

To be written
