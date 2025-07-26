import os


def create_folder(basic_path, session_id, child_dir):
    full_path = os.path.join(basic_path, session_id, child_dir)
    try:
        os.makedirs(full_path, exist_ok=True)
        return full_path
    except FileExistsError:
        return full_path
    except Exception as e:
        print(f"创建文件夹时出现错误: {e}")
        return None
