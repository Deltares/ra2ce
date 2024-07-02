.. _docker_user_guide:

Docker User Guide
=====================

Introduction
---------------------------------
This user guide shows a couple of thing:

a.  How to build a docker image from the ra2ce source tree and push it to a Dockerhub.
b.  How to run a simple model inside a created container and save the generated data for later display.
c.  (Future). How to get ra2ce plus displayer up and running in a standard Kubernetes environment.

In the addendum I will explain how to install Docker desktop on Windows and Docker on Ubuntu or Redhat like servers,
but since this can be changed outside this repository, it is probably best to use:

i.   For Windows-like systems: https://www.docker.com/products/docker-desktop/
     There is a good alternative (https://podman-desktop.io/) which works a little differen, but with the same
     outcome (at least for ra2ce).
	
ii.	 For Ubuntu-like systems: https://docs.docker.com/engine/install/ubuntu/

iii. For Redhat-like systems: https://docs.docker.com/desktop/install/linux-install/

iv.  For MacOS there is: https://docs.docker.com/desktop/install/mac-install/ (the writer of this document doesn't have
     much experience with a Mac.

Shown is the bash prompt, but when using Docker Desktop with Linux Containers enables, a Powershell also will do.

How to build a docker image from the ra2ce source tree
------------------------------------------------------

Assuming access to a Linux box with Docker installed, or a Docker Desktop with "Switch to Linux Containers". You can do the 
following:

.. parsed-literal::

    $ git clone git@github.com:Deltares/ra2ce.git
    $ cd ra2ce
    $ docker build -t ra2ce:latest .

These instructions will build a docker image. After a good while, you should end up with:

.. parsed-literal::

    $ docker images
    REPOSITORY                   TAG       IMAGE ID       CREATED             SIZE
    ra2ce                        latest    dd5dc5fe79ba   45 minutes ago      1.01GB

Remark that this is a local image only (it only exists on the server or laptop you build it). To share it with other team members, you should push this to a docker hub. This operation entails the following.

a.  Login to your dockerhub account (go to https://hub.docker.com/ if you don't have that yet):

.. parsed-literal::

    $ docker login
    Login with your Docker ID to push and pull images from Docker Hub. If you don't have a Docker ID, head over to https://hub.docker.com to create one.
    Username: willemdeltares
    Password:
    WARNING! Your password will be stored unencrypted in /u/noorduin/.docker/config.json.
    Configure a credential helper to remove this warning. See
    https://docs.docker.com/engine/reference/commandline/login/#credentials-store

    Login Succeeded

b.  Retag the image:

.. parsed-literal::

    $ docker tag ra2ce:latest willemdeltares/ra2ce:latest

c.  Pushing the image to the dockerhub:

.. parsed-literal::

    $ sudo docker push willemdeltares/ra2ce:latest

If all is well, you can login to the dockerhub account and see the image yourself.


Simple run
------------

On probably another laptop you can do the following:

.. parsed-literal::

    noorduin@c-teamcity08065 ~/development/ra2ce/docs/docker (noorduin_docker_k8s)$ docker pull willemdeltares/ra2ce:latest
    latest: Pulling from willemdeltares/race
    4db1b89c0bd1: Pull complete
    d78e3c519d33: Pull complete
    8219ddbde264: Pull complete
    ....
    d86857fa3e39: Pull complete
    3a05d3e367e1: Pull complete
    Digest: sha256:1c1cee508e498e7e58e01661b3c4047e458e936720ce11b8a242fae8375b1c7f
    Status: Downloaded newer image for willemdeltares/race:latest
    docker.io/willemdeltares/race:latest

    noorduin@c-teamcity08065 ~/development/ra2ce/docs/docker (noorduin_docker_k8s)$ docker run -d -p 8080:8080 ra2ce:latest
    
	noorduin@c-teamcity08065 ~/development/ra2ce/docs/docker (noorduin_docker_k8s)$ docker ps
    CONTAINER ID   IMAGE          COMMAND                  CREATED          STATUS          PORTS                    NAMES
    43ca6b0aef08   ra2ce:latest   "/usr/local/bin/_ent…"   23 minutes ago   Up 23 minutes   0.0.0.0:8080->8080/tcp   keen_bose

Now go to http://localhost:8080 and give in the default password (if you don't know it, try the name of this project, lowercase with the 2 in it).


Mounting in projects
------------------------

When run as in "Simple run", you only get what is bundled within the Docker image of ra2ce itself. Above that, when the container is 
stopped in some matter, the data is gone. to remedy this, we can mount in a custom based directory in the Docker Container. Like in the following:

a.	Make a standard ra2ce project like this:

.. parsed-literal::

        +--- example01
	    |   +--- .ipynb_checkpoints
    	|   |   +--- test-checkpoint.ipynb
    	|   +--- analysis.ini
    	|   +--- cache
    	|   +--- input
    	|   +--- network.ini
    	|   +--- output
    	|   |   +--- network.ini
    	|   +--- static
    	|   |   +--- hazard
    	|   |   +--- network
    	|   |   |   +--- Delft.geojson
    	|   |   +--- output_graph
    	|   +--- test.ipynb
	
b.  Start the container as follows:

.. parsed-literal::

        C:\Users\noorduin\development\ra2ce_inputs> docker run -d -v C:\Users\noorduin\development\ra2ce_inputs\project\:/home/mambauser/sample -p 8081:8080 ra2ce:latest
        9d95083de344c27a7009a65b57700e3db32eb72f33ebf605376a41587d19bd81
	
        C:\Users\noorduin\development\ra2ce_inputs> docker ps
        CONTAINER ID   IMAGE          COMMAND                  CREATED          STATUS          PORTS                    NAMES
        7c000d7ae8ae   ra2ce:latest   "/usr/local/bin/_ent…"   23 seconds ago   Up 22 seconds   0.0.0.0:8081->8080/tcp   adoring_roentgen
		43ca6b0aef08   ra2ce:latest   "/usr/local/bin/_ent…"   2 hours ago      Up 2 hours      0.0.0.0:8080->8080/tcp   keen_bose
    
Notice that we have two ra2ce-applications now, one available on http://localhost:8080 and one new on http://localhost:8081. The first interface
knows nothing of the second here. When you go to http://localhost:8081 you can see the data folder mounted in /home/mambauser as a directory sample.
From there, you can start test.ipynb.

Trouble shooting
---------------------------------

In the Docker world, there are a lot of things that go wrong (from forgetting the BIOS setting mentioned in the Addendum) to
not enough user rights on Linux). It is best to refer to www.docker.com or one of there foras for those. Here, we focuss on the 
errors and warning you could see in the combination Ra2ce and docker.

1.	When I browse to http://localhost:8080 I can't see the interface. Or when I log in, I can't see the project.

	Jupyter seems to be very cookie-aware. Try to delete the cookies or use a private browser-session.
	


Addendum
---------------------------------

1.   Simple Docker Desktop setup on Windows:
     
     **Step 1: BIOS Prerequisites**
	 
     There is a setting in the BIOS (or a modern equivalent of that) that makes it possible to virtualize the CPU. 
     Unfortunately every Hardware Manufacturer has its own name for it and position in the BIOS.
	 
     **Step 2: Containers and Hyper-V**

     Run the following in an Administrator's Powershell::
	 
          PS C:> Enable-WindowsOptionalFeature -Online -FeatureName $("Microsoft-Hyper-V", "Containers") -All
		 
     Then reboot your PC.
	 
     **Step 3: Install wsl-1 and wsl-2**
	 
     See also: https://learn.microsoft.com/en-us/windows/wsl/install. Make sure that you reboot afterwards
	 
     **Step 4: Install Docker desktop**
	 
     After step 1 and 2 it should be posssible to download and install Docker Desktop for Windows (see also
     https://docs.docker.com/desktop/install/windows-install/).
	 
     **Step 5: Switch to Linux Containers**
	 
     Ra2ce is based on a Linux image and it is hard too tell the default at forehand. If Docker Desktop is 
     started up correctly, there should be a Whale-like icon amongst your "Hidden Icons". When you right-click
     it you can swich to either Linux or Windows Containers. For Ra2ce it's important to choose "Linux containers".