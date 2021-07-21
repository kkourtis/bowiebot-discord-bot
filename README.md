# bowiebot-discord-bot
Discord bot that plays sound clips then leaves the server. If you see this, RIP bowiebot. I no longer want to work on you. It was lazily made with zero regards to best practicing if it existed. This is just for archival purposes but if you wanna do something with it be my guest.

Below are the steps I would take to rebuild bowiebot in a brand new instance. You may need to modify them to fit your system. This was built on a CentOS 7.6 x64 VPS run on a Digital Ocean 1GB RAM, 25GB Storage + 1GB Expandable Storage.

**Create a bowiebot user. (It is named bowiebot to make creating the psql database easier.)**

`adduser bowiebot`

`passwd bowiebot`

`usermod -aG wheel bowiebot  (do this if you want it to have sudo)`

**Install Python3.6**

`sudo yum -y install python36u`

`sudo yum -y install python36u-pip`

`sudo yum -y install python36u-devel`

**Install Discord.py**

`python3.7 -m pip install –upgrade pip`

`python3.7 -m pip install -U discord.py[voice]`

**Install some dependencies**

`sudo python3.6 -m pip install tinytag`

`sudo python3.6 -m pip install psutil`

**Install opus-tools**

`sudo yum install opus-tools`

**Install tmux (allows bot to run after dropping ssh)**

`sudo yum install tmux`

**Install FFMPEG**

`sudo rpm --import http://li.nux.ro/download/nux/RPM-GPG-KEY-nux.ro`

`sudo rpm -Uvh http://li.nux.ro/download/nux/dextop/el7/x86_64/nux-dextop-release-0-5.el7.nux.noarch.rpm`

`sudo yum update -y`

`sudo yum install ffmpeg ffmpeg-devel -y`

**Install PostgreSQL**


`sudo yum install postgresql-server postgresql-contrib`

`sudo postgresql-setup initdb`

`sudo systemctl start postgresql`

`sudo systemctl enable postgresql`

Edit PSQL config to allow password auth

`sudo vi /var/lib/pgsql/data/pg_hba.conf`

**Under IPv4 local connections and IPv6 Local Connections, change `ident` to `md5`**

Press ESC to exit insert mode.

Enter :w to save changes.

Enter :q to Quit Vi

**Start PSQL**

`sudo systemctl start postgresql`

`sudo systemctl enable postgresql`


**Create the bowiebot Postgres user**

`sudo -i -u postgres`

`createuser -P bowiebot`

`createdb bowiebot`

You will have been given an old backup of the PSQL database. This will strictly be used to generate the schema. This is how you would import it. (If you dont have it just ask)

`psql -U bowiebot bowiebot < [dump_name]`

Just msg me if you have questions I prob won't be able to answer but worth a shot.



After that just slap em with the big ol'

`python3.6 bot.py`

and let your dreams come true.









