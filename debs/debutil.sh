#!/bin/bash

while [[ $# -gt 0 ]];
do
  case $1 in
    -s|-Section)
      Section=$2
      shift
      shift
      ;;
    -d|-Deb)
     original_package="$2"
      shift
      shift
      ;;
  esac
done

Modifi() {
# 定义修改后的软件包路径和名称
modified_package="${original_package%.*}.deb"

# 创建临时目录用于解压缩软件包
temp_dir=$(mktemp -d)

# 解压缩软件包到临时目录
dpkg-deb -R "$original_package" "$temp_dir"

# 修改控制文件中的信息
control_file="$temp_dir/DEBIAN/control"
if [ -n "$Section" ]; then
  sed -i "s|Section: .*|Section: $Section|g" "$control_file"
else
  dpkg-scanpackages $original_package
fi
# 重新打包软件包
dpkg-deb -b "$temp_dir" "./modified/$modified_package"

# 删除临时目录
rm -rf "$temp_dir"

echo "修改后的软件包已生成：$modified_package"
}
if [ -n "$Section" ]; then
  Modifi
else
  dpkg-scanpackages $original_package
fi

