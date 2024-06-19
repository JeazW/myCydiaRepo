mkdir -p ../renameabcydia
for i in `ls|grep -v deb.tmp|grep -v rename.sh`
do
sudo dpkg-scanpackages $i |grep Name|awk -F':' '{print $2}'|sed 's#^ ##g' > deb.tmp
NAME=`cat deb.tmp | grep -v dpkg`
mv $i "${NAME}"
done
