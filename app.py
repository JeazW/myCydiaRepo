import re
import os
import shutil
from flask import Flask, render_template, redirect, url_for, request
import subprocess
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # 设置一个密钥，用于加密用户凭证

login_manager = LoginManager()
login_manager.init_app(app)

# 定义用户模型
class User(UserMixin):
    def __init__(self, username, password):
        self.id = username
        self.password = password

# 模拟一个用户数据库
users = {
    'admin': User('admin', 'password'),
}

@login_manager.user_loader
def load_user(user_id):
    return users.get(user_id)

@login_manager.unauthorized_handler
def unauthorized():
    return redirect(url_for('login'))

@app.route('/list')
@login_required
def list_packages():
    packages = parse_packages_file('Packages')  # 解析Packages文件，获取包信息
    return render_template('list.html', packages=packages)

@app.route('/package/<name>')
@login_required
def package_details(name):
    packages = parse_packages_file('Packages')
    for package in packages:
        if package['name'] == name:
            return render_template('package.html', package=package)
    return redirect(url_for('list_packages'))

@app.route('/list/refresh', methods=['GET'])
@login_required
def refresh_list():
    subprocess.run(['bash', 'update.sh'])
    return '', 200

@app.route('/package/<name>/edit', methods=['POST'])
@login_required
def edit_package(name):
    section = request.form['section']
    homepage = request.form['homepage']
    description = request.form['description']
    original_package = request.form['original_package']
    modified_package = modify_package_fields(original_package, section, homepage, description)
    return redirect(url_for('package_details', name=name))

@app.route('/package/<name>/delete', methods=['POST'])
@login_required
def delete_package(name):
    package = get_package_by_name(name)
    if package:
        deb_file = package['filename']
        os.remove(deb_file)
        subprocess.run(['bash', 'update.sh'])
    return redirect(url_for('list_packages'))

@app.route('/upload', methods=['POST'])
@login_required
def upload():
    file = request.files['file']
    if file and file.filename.endswith('.deb'):
        save_path = os.path.join('debs', file.filename)
        file.save(save_path)
        subprocess.run(['bash', 'update.sh'])
        return '', 200  # 返回空响应和状态码200表示上传成功
    else:
        return '', 400  # 返回空响应和状态码400表示上传失败

def parse_packages_file(filename):
    packages = []
    with open(filename, 'r') as file:
        package_info = {}
        for line in file:
            line = line.strip()
            if line.startswith('Package:'):
                if package_info:  # 如果已经有包的信息，将其添加到列表中
                    packages.append(package_info)
                package_info = {'name': line.split('Package: ')[1]}
            elif line.startswith('Version:'):
                package_info['version'] = line.split('Version: ')[1]
            elif line.startswith('Depends:'):
                package_info['depends'] = line.split('Depends: ')[1]
            elif line.startswith('Filename:'):
                package_info['filename'] = line.split('Filename: ')[1]
            elif line.startswith('Size:'):
                package_info['size'] = line.split('Size: ')[1]
            elif line.startswith('Section:'):
                package_info['section'] = line.split('Section: ')[1]
            elif line.startswith('Homepage:'):
                package_info['homepage'] = line.split('Homepage: ')[1]
            elif line.startswith('Description:'):
                package_info['description'] = line.split('Description: ')[1]
            # 添加其他您需要的字段解析逻辑
        if package_info:  # 处理最后一个包的信息
            packages.append(package_info)
    return packages

def modify_package_fields(original_package, section, homepage, description):
    modified_package = original_package.replace('.deb', '.deb')
    modify_deb_package(original_package, modified_package, section, homepage, description)
    return modified_package

def modify_deb_package(original_package, modified_package, section, homepage, description):
    # 创建临时目录用于解压缩软件包
    temp_dir = 'tmp_dir'
    os.makedirs(temp_dir, exist_ok=True)

    # 解压缩软件包到临时目录
    subprocess.run(['dpkg-deb', '-R', original_package, temp_dir])

    # 修改控制文件中的字段
    control_file = os.path.join(temp_dir, 'DEBIAN', 'control')
    with open(control_file, 'r') as file:
        control_content = file.read()

    control_content = re.sub(r'^Section: .*', f'Section: {section}', control_content, flags=re.MULTILINE)
    control_content = re.sub(r'^Homepage: .*', f'Homepage: {homepage}', control_content, flags=re.MULTILINE)
    control_content = re.sub(r'^Description: .*', f'Description: {description}', control_content, flags=re.MULTILINE)

    with open(control_file, 'w') as file:
        file.write(control_content)

    # 重新打包软件包
    subprocess.run(['dpkg-deb', '-b', temp_dir, modified_package])

    # 删除临时目录
    shutil.rmtree(temp_dir)

    # 执行更新信息的操作
    subprocess.run(['bash', 'update.sh'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = users.get(username)

        if user and user.password == password:
            login_user(user)  # 登录用户
            return redirect(url_for('list_packages'))
        else:
            return render_template('login.html', error=True)

    return render_template('login.html')

@app.route('/logout')
@login_required  # 要求用户登录才能注销
def logout():
    logout_user()  # 注销用户
    return redirect(url_for('list_packages'))

def get_package_by_name(name):
    packages = parse_packages_file('Packages')
    for package in packages:
        if package['name'] == name:
            return package
    return None

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8085, debug=True)

