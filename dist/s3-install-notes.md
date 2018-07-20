The iRODS install is done as an ordinary user but you need sudo access. More information can be found at http://slides.com/jasoncoposky/getting-started-gpn2018#
# iRODS install starts here. 
```
sudo apt-get update
sudo apt-get -y install git g++ make python-dev help2man unixodbc libfuse-dev libcurl4-gnutls-dev libbz2-dev zlib1g-dev libpam0g-dev libssl-dev libxml2-dev libkrb5-dev unixodbc-dev libjson-perl python-psutil python-jsonschema super python-exif odbc-postgresql
sudo apt-get -y install postgresql
sudo su - postgres
wget -qO - https://packages.irods.org/irods-signing-key.asc | sudo apt-key add -
echo "deb [arch=amd64] https://packages.irods.org/apt/ $(lsb_release -sc) main" |   sudo tee /etc/apt/sources.list.d/renci-irods.list
sudo apt-get update
sudo apt-get -y install irods-server irods-database-plugin-postgres
sudo apt-get -y install irods-dev*
sudo apt-get -y install irods-extern*
sudo python /var/lib/irods/scripts/setup_irods.py < /var/lib/irods/packaging/localhost_setup_postgres.input
```
# End of iRODS install

The following is known to work on Ubuntu 16 (Xenial) with the stock version of iRODS 4.2.3. We could always add more binaries to the repo, but if you are using any other iRODS you may need to rebuild the S3 driver.
# Start of S3 plugin install
```
mkdir repos
cd repos
git clone https://github.com/heliumdatacommons/irods_resource_plugin_s3.git
cd irods_resource_plugin_s3/dist/xenial
```

These are the 2 AWS SDK libraries we need
```
sudo cp *.so /usr/local/lib
```

This installs the plugin
```
sudo dpkg -i irods-resource-plugin-s3_2.3.0~xenial_amd64.deb
```

These two lines are just to check!
```
sudo ls -alrt /usr/local/lib
sudo ls -alrt /usr/lib/irods/plugins/resources/
```
# End of s3 plugin install

# Start of S3 plugin configuration
```
sudo su - irods
```

Make the file that contains the s3 irods user credentials.

```
mkdir /var/lib/irods/.ssh
vi /var/lib/irods/.ssh/irods-s3-resource-1.keypair
```

Contents of the credential file are:
```
The iRODS account key identifier.  Ends in FGFA
The iRODS account secret. Ends in Jj9r
```

Make the file that contains the needed ARN information. 
```
vi /etc/irods/irods-s3-arn.config
```

Contents of the ARN file are
```
The bucket specific ARN string: arn:aws:iam::xxxxxxxxxxxx:role/developer_access_gtex
The length of time for which the temporary credential is valid in seconds: 900
```

Make the compound resource
```
iadmin mkresc AWSCloudParent-ARN-test compound
```

Make the cache resource on the local file system. Note that we add .ec2.internal to the hostname,
```
iadmin mkresc AWSCloudCache-ARN-test unixfilesystem ip-172-31-27-229.ec2.internal:/var/lib/irods/AWSVaults
```

Make the archive resource that points to the NIH bucket. Note that we add .ec2.internal to the hostname. We also
 switch on role assumption with S3_ENABLE_ROLE_ASSUMPTION=1 and specify the name of the file with the ARN information
 that we created above using S3_ASSUME_ROLE_FILE=/etc/irods/irods-s3-arn.config
```
iadmin mkresc AWSCloudArchive-ARN-test s3 ip-172-31-27-229.ec2.internal:nih-nhgri-datacommons "S3_DEFAULT_HOSTNAME=s3.amazonaws.com;S3_AUTH_FILE=/var/lib/irods/.ssh/irods-s3-resource-1.keypair;S3_RETRY_COUNT=10;S3_WAIT_TIME_SEC=10;S3_PROTO=HTTPS;S3_ENABLE_MPU=1;S3_ENABLE_ROLE_ASSUMPTION=1;S3_ASSUME_ROLE_FILE=/etc/irods/irods-s3-arn.config"
```

Add the cache and archive resources to the parent.
```
iadmin addchildtoresc AWSCloudParent-ARN-test AWSCloudCache-ARN-test cache
iadmin addchildtoresc AWSCloudParent-ARN-test AWSCloudArchive-ARN-test archive
```

Register the NIH hello world file
```
ireg -R AWSCloudArchive-ARN-test /nih-nhgri-datacommons/helloworld.txt /tempZone/home/rods/helloworld.txt
```

Retrieve the hello world file.
```
iget helloworld.txt
```

Confirm the results. Replica 0 is the registered copy in the NIH bucket, Replica 1 is the copy in the cache.
```
irods@ip-172-31-27-229:~$ ils -l
/tempZone/home/rods:
  rods              0 AWSCloudParent-ARN-test;AWSCloudArchive-ARN-test           12 2018-07-19.20:06 & helloworld.txt
  rods              1 AWSCloudParent-ARN-test;AWSCloudCache-ARN-test           12 2018-07-19.20:07 & helloworld.txt
```

Cat the local copy of the file to be sure
```
irods@ip-172-31-27-229:~$ cat helloworld.txt
hello world
```

