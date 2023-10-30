import argparse as aps

import cmd2 as cmd
from cmd2 import with_argparser

from Command.DeleteCommand import DeleteCommand
from Command.DirTreeCommand import DirTreeCommand
from Command.InsertCommand import InsertCommand
from Command.ListCommand import ListCommand
from Command.ListTreeCommand import ListTreeCommand
from Command.LoadCommand import LoadCommand
from Command.SaveCommand import SaveCommand
from Command.UndoCommand import UndoCommand

current_load_file = ""  # initialize global variable a，为空表示当前未加载文件
command_stack = []  # 保存可以被undo的编辑指令
input_history = []  # 保存用户的输入记录


class NewInput(cmd.Cmd):
    redo_command = None

    def __init__(self):
        super().__init__()

    '''
    # 使用 cmd2 处理参数，解析命令词后的 opt 字符串，较为灵活

    def do_checkopt(self, opt):
        if len(opt)==0 or opt.isspace():
            print("no opt")
        else:
            opts = [int(i) for i in opt.split(' ')]
            print(opts)

    # 使用 cmd2 + argparse 配置命令行参数, eg. plus 1 2

    argparse_plus=aps.ArgumentParser()
    argparse_plus.add_argument('num1',type=int,help='arg1_help')
    argparse_plus.add_argument('num2',type=int,help='arg1_help')
    @with_argparser(argparse_plus)
    def do_plus(self,opt):
        print(opt.num1 + opt.num2)

    # 注：使用 argparse 隐含参数检查，否则可以调用 check_opt_num(opt,num) 检查参数个数至少为 num
    '''

    # exit
    def do_exit(self, line):
        print("Exiting the program...")
        return True

    # load 文件路径
    argparse_load = aps.ArgumentParser()
    argparse_load.add_argument('file_path', type=str, help='path of file')

    @with_argparser(argparse_load)
    def do_load(self, opt):
        input_history.append('load' + opt.file_path)
        # 参数检查: argparse 隐含
        # 构建命令，加入 command_stack 并执行
        command = LoadCommand(opt.file_path)
        command_stack.clear()
        if command.execute():
            # 加载成功, 改变命令行提示词
            global current_load_file
            current_load_file = opt.file_path
            self.prompt = "<" + opt.file_path + "> "

    # save
    # 保存文件
    def do_save(self, opt):
        input_history.append('save' + opt)
        global current_load_file
        if not self.check_has_load():
            return
        save_command = SaveCommand(current_load_file)
        command_stack.clear()
        save_command.execute()

        current_load_file = ""
        # 改变命令行提示词
        self.prompt = "<Editor> "

    # list
    # 以文本形式显示当前编辑的内容。
    def do_list(self, opt):
        input_history.append('list' + opt)
        list_command = ListCommand()
        list_command.execute()

    # list_tree
    # 以树形结构显示当前编辑的内容。
    def do_list_tree(self, opt):
        input_history.append('list-tree' + opt)
        list_command = ListTreeCommand()
        list_command.execute()

    # dir-tree
    # 以树形结构显示指定目录（标题）下的内容。
    def do_dir_tree(self, opt):
        input_history.append('dir-tree' + opt)
        list_command = DirTreeCommand(opt)
        list_command.execute()

    # insert [行号] 标题/文本
    # 行号可以省略，若省略则默认在文件末尾插入内容
    def do_insert(self, opt):
        input_history.append('insert' + ' ' + opt)
        # print(input_history)
        if not self.check_has_load():
            return
        if not self.check_opt_num(opt, 1):  # 至少一个参数
            return
        insert_command = InsertCommand(opt)
        command_stack.append(insert_command)
        # print(command_stack)
        insert_command.execute()
        global redo_command
        redo_command = None

    # append_head 标题/文本
    # 在文件起始位置插入标题或文本。
    def do_append_head(self, opt):
        opt = '1' + ' ' + opt
        self.do_insert(opt)

    # append-tail 标题/文本
    # 在文件末尾位置插入标题或文本。
    def do_append_tail(self, opt):
        self.do_insert(opt)

    # delete 标题/文本 或 delete 行号
    # 如果指定行号，则删除指定行。
    # 当删除的是标题时，其子标题和内容不会被删除。
    # 对多个一样的行，只会删除第一个
    def do_delete(self, opt):
        input_history.append('delete' + opt)
        if not self.check_has_load():
            return
        if not self.check_opt_num(opt, 1):  # 至少一个参数
            return
        delete_command = DeleteCommand(opt)
        command_stack.append(delete_command)
        delete_command.execute()
        global redo_command
        redo_command = None

    # undo
    # 撤销上一次执行的编辑命令，返回到执行该命令前的状态。不适用于非编辑命令。
    def do_undo(self, opt):
        input_history.append('undo' + opt)
        if len(command_stack) == 0:
            return
        c = command_stack.pop()  # pop()删除并返回末尾元素。
        c.undo()

        undo_tag = UndoCommand()
        command_stack.append(undo_tag)
        # 定义全局变量，用于保存undo之前的一个命令
        global redo_command
        redo_command = c

    # redo
    # 只有上一个编辑命令是 undo 时，才允许执行 redo。
    def do_redo(self, opt):
        input_history.append('redo' + opt)
        global redo_command
        if redo_command is None or len(command_stack) == 0:
            print("prompt: no command to redo")
            return
        else:
            # redo就是对undo的命令重新执行一遍，执行完后清空redo_command中的内容
            redo_command.execute()
            redo_command = None

    # check opt_num >= num
    def check_opt_num(self, opt, num):
        if num <= 0:
            return True
        # 以下，至少要有一个参数
        if len(opt) == 0 or opt.isspace():
            print("prompt: no opt, you need at least " + str(num) + " opts")
            return False
        opt_num = 0
        for i in opt.split(' '):
            opt_num += 1
        if opt_num < num:
            print("prompt: " + str(opt_num) + " opts, you need at least " + str(num) + " opts")
            return False
        return True

    # check a file has been loaded
    def check_has_load(self):
        if len(current_load_file) == 0:
            print("prompt: you need to load a file firstly.")
            return False
        return True

    def set_prompt(self, line):
        self.prompt = line
        return self


if __name__ == '__main__':
    welcome = "\n\
    ***********************************************************************************\n\
       __  __            _       _                       ______    _ _ _               \n\
      |  \/  |          | |     | |                     |  ____|  | (_) |              \n\
      | \  / | __ _ _ __| | ____| | _____      ___ __   | |__   __| |_| |_ ___  _ __   \n\
      | |\/| |/ _` | '__| |/ / _` |/ _ \ \ /\ / / '_ \  |  __| / _` | | __/ _ \| '__|  \n\
      | |  | | (_| | |  |   < (_| | (_) \ V  V /| | | | | |___| (_| | | || (_) | |     \n\
      |_|  |_|\__,_|_|  |_|\_\__,_|\___/ \_/\_/ |_| |_| |______\__,_|_|\__\___/|_|     \n\
                                                                                       \n\
    ***********************************************************************************\n\
    "
    print(welcome)
    NewInput().set_prompt("<Editor> ").cmdloop()
