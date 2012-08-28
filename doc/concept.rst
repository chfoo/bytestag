Concept
=======

.. note::

   *Bytestag shares files publicly.* As a result, expert users may inspect
   incoming file parts.
   
   (In the future, it may be possible files privately with only a select few.)

Sharing Files
++++++++++++++

Files are shared by publishing or replicating files to other computers.

.. image:: images/file_part_publication.png
   :alt: This image is described by the following.
   
   Publishing a file.

1. A file or a collection of files is selected.
2. The software breaks the files into parts and generates a info file that 
   describes the files.
3. The software computes the destination of each part. Then, it sends
   the info file and file parts to other computers. Each part has its own
   unique ID.
4. An ID of the info file is shared among users.

Files expire after 1 day after publication so users sharing files will need
to ensure the computer is running frequently through time.

As the popularity of a file increases, the number of publishers increase.
As a result, each individual publisher does not need their computer on 
frequently.

Downloading Files
++++++++++++++++++

Files are downloaded by fetching the info file and, using the information 
within the info file, downloads the file parts from other computers.

.. image:: images/file_part_download.png
   :alt: This image is described by the following.
   
   Downloading a file.

1. An ID of the info file is obtained.
2. The info file is downloaded using the info file ID.
3. The software reads the info file and determines possible computers with
   the file parts.
4. Computers send the file parts back.

Maintaining the Network
+++++++++++++++++++++++

Because files are pushed to other computers, the amount of data shared is
limited by the disk space and online availability of the network. 
As such, it is necessary that all users are prepared to donate plenty of 
bandwidth, disk space, and computer uptime.

Fact:
If half of the world's internet users [1]_ [2]_ each donated 1 gigabyte of 
disk space, then the network would hold 1000 petabytes! (That's 172 times
of Archive.org! [3]_)


.. [1] Internet users as percentage of population, World: 30% (2010, World Bank).
.. [2] Population, World: 7 billion (2011, World Bank).
.. [3] At 5.8 PB. `<http://archive.org/web/petabox.php>`_ December 2010.
