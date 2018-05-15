import sys

import os
from pysideuic import compileUi

if __name__ == '__main__':
    '''
    A '.ui' file is expected to be passed in as the first argument to this script.  The second argument is the directory
    into which to write the Python form of the ui file.  Both the file and the directory should be described relative
    to the root directory of the repository.

    Script has been used with the following arguments:
     - mapclientplugins/meshgeneratorstep/qt/meshgeneratorwidget.ui mapclientplugins/meshgeneratorstep/view
    '''
    if len(sys.argv) > 2:
        ui_file = sys.argv[1]
        out_dir = sys.argv[2]
    else:
        print('Error: must supply filenames through the command line.')
        sys.exit(-1)

    file_basename = os.path.basename(ui_file)
    file_root_name = os.path.splitext(file_basename)[0]
    abs_script_directory = os.path.realpath(os.path.dirname(__file__))

    repo_root_dir = os.path.realpath(os.path.join(abs_script_directory, '..'))
    os.chdir(repo_root_dir)
    abs_path_to_file = os.path.join(repo_root_dir, ui_file)

    ui_file_output_directory = os.path.join(repo_root_dir, out_dir)

    if not os.path.exists(os.path.join(repo_root_dir, ui_file_output_directory)):
        print('Error: output directory "%s" does not exist.' % (os.path.join(repo_root_dir, ui_file_output_directory)))
        sys.exit(-2)

    abs_path_to_ui_file = os.path.join(repo_root_dir, ui_file_output_directory, 'ui_' + file_root_name + '.py')

    with open(ui_file, 'r') as f:
        with open(abs_path_to_ui_file, 'w') as g:
            print('Compiling ui file "%s" and saving in "%s".' % (abs_path_to_file, abs_path_to_ui_file))
            compileUi(f, g, from_imports=True)
