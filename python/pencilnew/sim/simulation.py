
# simulation.py
#
# Create simulation object to operate on.
#
# Authors:
# A. Schreiber (aschreiber@mpia.de)
#
"""
Contains the simulation class which can be used to directly create, access and
manipulate simulations.
"""

def simulation(*args, **kwargs):
    """
    Generate simulation object from parameters.
    Simulation objects are containers for simulations. pencil can work with
    several of them at once if stored in a list or dictionary.

    Args for Constructor:
        path:		path to simulation, default = '.'
        hidden:     set True to set hidden flag, default is False
        quiet:      suppress irrelevant output, default False

    Properties:
        self.name:          name of
        self.path:          path to simulation
        self.datadir:      path to simulation data-dir (./data/)
        self.pc_dir:        path to simulation pc-dir (./pc/)
        self.pc_datadir:   path to simulation pendir in datadir (data/pc/)
        self.components:    list of files which are nessecarry components of the simulation
        self.optionals:     list of files which are optional components of the simulation
        self.hidden:        Default is False, if True this simulation will be ignored by pencil
        self.param:         list of param file
        self.grid:          grid object
    """

    return __Simulation__(*args, **kwargs)

class __Simulation__(object):
    """
    Simulation object.
    """

    def __init__(self, path='.', hidden=False, quiet=False):
        import os
        from os.path import join
        from os.path import exists
        from os.path import split
        #from pen.intern.hash_sim import hash_sim

        path = path.strip()
        if path.endswith('/'): path = path[:-1]
        self.name = split(path)[-1]     # find out name and store it
        if self.name == '.' or self.name == '': self.name = split(os.getcwd())[-1]

        self.path = os.path.abspath(path)   # store paths
        if (not quiet): print('# Creating Simulation object for '+self.path)
        self.datadir = join(self.path,'data')
        self.pc_dir = join(self.path,'pc')
        self.pc_datadir = join(self.path,'data','pc')

        self.components = ['src/cparam.local',      # core files of a simulation run
                           'src/Makefile.local',
                           'start.in',
                           'run.in',
                           'print.in']
        self.quantity_searchables = ['src/cparam.local','start.in', 'run.in']    # files in which quanitities can be searched
        self.optionals = ['*.in', '*.py', 'submit*']    # optinal files that should stick with the simulation when copied

        self.hidden = hidden                # hidden is default False
        self.param = False
        self.grid = False
        self.ghost_grid = False
        self = self.update(quiet=quiet)                   # auto-update, i.e. read param.nml
        # Done

    def copy(self, path_root='.', name=False, optionals=True, quiet=True, rename_submit_scripts=False, OVERWRITE=False):
        """This method does a copy of the simulation object by creating a new directory 'name' in 'path_root' and copy all simulation components and optionals to his directory.
        This method neither links/compiles the simulation, nor creates data dir nor does overwrite anything.

        Submit Script Rename:
            Name in submit scripts will be renamed if possible! Submit scripts will be identified by submit* plus appearenace of old simulation name inside, latter will be renamed!

        Args:
            path_root:      Dir to create new sim.-folder(sim.-name) inside. This folder will be created if not existing!
            name:           Name of new simulation, will be used as folder name. Rename will also happen in submit script if found. Simulation folders is not allowed to preexist!!
            optionals:      Add list of further files to be copied. Wildcasts allowed according to glob module! Set True to use self.optionals.
            quiet:          Set True to suppress output.
            rename_submit_scripts:   Set False if no renames shall be performed in subnmit* files
            OVERWRITE:      Set True to overwrite no matter what happens!
        """
        from os import listdir
        from os.path import exists, join, abspath, basename
        from shutil import copyfile
        from glob import glob
        from numpy import size
        from pencilnew.io import mkdir
        from pencilnew.sim import is_sim_dir
        from pencilnew import get_sim
        from pencilnew.io import mkdir, get_systemid, debug_breakpoint
        from pencilnew.sim import is_sim_dir

        # set up paths
        if path_root == False or type(path_root) != type('string'):
            print('! ERROR: No path_root specified to copy the simulation to.');
            return False
        path_root = abspath(path_root)          # simulation root dir

        # name and folder of new simulation
        # but keep name of old if sim with old name is NOT existing in NEW directory
        if name == False:
            name = self.name
        if exists(join(path_root, self.name)):
            name = name+'_copy'
            if exists(join(path_root, name)):
                name = name + str(size([f for f in listdir(path_root) if f.startswith(name)]))
            print('? Warning: No name specified and simulation with that name already found! New simulation name now '+name)
        path_newsim = join(path_root, name)     # simulation abspath
        path_newsim_src = join(path_newsim, 'src')

        if type(optionals) == type(['list']): optionals = self.optionals + optionals          # optional files to be copied
        if optionals == True: optionals = self.optionals
        if type(optionals) == type('string'): optionals = [optionals]
        if type(optionals) != type(['list']): print('! ERROR: optionals must be of type list!')

        tmp = []
        for opt in optionals:
            files = glob(join(self.path, opt))
            for f in files:
                tmp.append(basename(f))
        optionals = tmp

        ## check if the copy was already created
        if is_sim_dir(path_newsim):
            if not quiet: print('? WARNING: Simulation already exists. Returning with existing simulation.')
            return get_sim(path_newsim, quiet=quiet)

        ## expand list of optionals wildcasts

        # check existance of path_root+name, a reason to stop to not overwrite anything
        if OVERWRITE==False and exists(path_newsim):
            print('! ERROR: Folder to copy simulation to already exists!\n! -> '+path_newsim)
            return False

        # check existance of self.components
        for comp in self.components:
            if not exists(join(self.path, comp)):
                print('! ERROR: Couldnt find component '+comp+' from simulation '+self.name+' at location '+join(self.path, comp))
                return False

        # check existance of optionals
        for opt in optionals:
            if not exists(join(self.path, opt)):
                print('! ERROR: Couldnt find optinal component '+opt+' from simulation '+self.name+' at location '+join(self.path, opt))
                return False

        # create folders
        if mkdir(path_newsim) == False and OVERWRITE==False:
            print('! ERROR: Couldnt create new simulation directory '+path_newsim+' !!')
            return False

        if mkdir(path_newsim_src) == False and OVERWRITE==False:
            print('! ERROR: Couldnt create new simulation src directory '+path_newsim_src+' !!')
            return False

        # copy files
        files_to_be_copied = []
        for f in self.components+optionals:
            f_path = abspath(join(self.path, f))
            copy_to = abspath(join(path_newsim, f))
            if f_path == copy_to:
                print('!! ERROR: file path f_path equal to destination copy_to. Debug this line manually!')
                debug_breakpoint()
            copyfile(f_path, copy_to)

        # modify name in submit script files
        if rename_submit_scripts:
            print('!! ERROR: Not implemented yet...  old version was not stable.')
            #for f in self.components+optionals:
                #if f.startswith('submit'):
                    #debug_breakpoint()
                    #system_name, raw_name, job_name_key, submit_scriptfile, submit_line = get_systemid()

        # done
        return get_sim(path_newsim)


    def update(self, quiet=True):
        """Update simulation object:
                - read param.nml
                - read grid and ghost grid
        """
        from os.path import exists
        from os.path import join
        from pencilnew.read import param
        from pencilnew.read import grid


        if self.param == False:
            try:
                if exists(join(self.datadir,'param.nml')):
                    param = param(quiet=quiet, datadir=self.datadir)
                    self.param = {}                     # read params into Simulation object
                    for key in dir(param):
                        if key.startswith('__'): continue
                        self.param[key] = getattr(param, key)
                else:
                    if not quiet: print('? WARNING: for '+self.path+'\n? Simulation has not run yet! Meaning: No param.nml found!')
            except:
                print('! ERROR: while reading param.nml for '+self.path)
                self.param = False

        if self.param != False and (self.grid == False or self.ghost_grid == False):
            try:                                # read grid only if param is not False
                self.grid = grid(datadir=self.datadir, trim=True, quiet=True)
                self.ghost_grid = grid(datadir=self.datadir, trim=False, quiet=True)
            except:
                if self.started() or (not quiet): print('? WARNING: Couldnt load grid for '+self.path)
                self.grid = False
                self.ghost_grid = False
        else:
            self.grid = False
            self.ghost_grid = False

        self.export()
        return self


    def hide(self):
        """Set hide flag True for this simulation. """
        self.hidden = True; self.export()


    def unhide(self):
        """Set hide flag False for this simulation. """
        self.hidden = False; self.export()


    def export(self):
        """Export simulation object to its root/.pc-dir"""
        from pencilnew.io import save
        if self == False: print('! ERROR: Simulation object is bool object and False!')
        save(self, name='sim', folder=self.pc_dir)


    def started(self):
        """Returns whether simulation has already started.
        This is indicated by existing time_series.dat in data directory."""
        from os.path import exists, realpath, join
        return exists(join(self.path, 'data', 'time_series.dat'))


    def compile(self, cleanall=True, fast=False, verbose=False):
        """Compiles the simulation. Per default the linking is done before the
        compiling process is called. This method will use your settings as
        defined in your .bashrc-file.

        Args:
            cleanall:     before calling pc_build, pc_build --cleanall is called
            verbose:      activate for verbosity
            fast:         set True for fast compilation
        """
        import pencilnew as pcn
        from os.path import join

        timestamp = pcn.io.timestamp()

        command = []
        if cleanall: command.append('pc_build --cleanall')
        if fast == True:
            command.append('pc_build --fast')
        else:
            command.append('pc_build')

        if verbose: print('! Compiling '+self.path)
        return self.bash(command=command,
                         verbose=verbose,
                         logfile=join(self.pc_dir, 'compilelog_'+timestamp))

    def build(self, cleanall=True, fast=False, verbose=False):
        """Same as compile()"""
        return self.compile(cleanall=cleanall, fast=fast, verbose=verbose)

    def bash(self, command, verbose=True, logfile=False):
        """Executes command in simulation diredctory.
        This method will use your settings as defined in your .bashrc-file.
        A log file will be produced within 'self.path/pc'-folder

        Args:
            - command:     command to be executed, can be a list of commands
            - verbose:     show output afterwards
        """
        import subprocess
        import pencilnew as pcn
        from os.path import join, realpath

        timestamp = pcn.io.timestamp()
        pcn.io.mkdir(self.pc_dir)
        if not type(logfile) == type('string'):
            logfile = join(self.pc_dir, 'bash_log_'+timestamp)

        commands = ['cd '+realpath(self.path)]
        #commands.append('source ~/.bashrc')
        #commands.append('shopt -s expand_aliases')

        if type(command) == type(['list']):
            for c in command:
                commands.append(c)
        elif type(command) == type('string'):
            commands.append(command)
        else:
            print('! ERROR: Couldnt understand the command parameter: '+str(command))

        with open(logfile, 'w') as f:
            rc = subprocess.call(['/bin/bash', '-i', '-c', ';'.join(commands)],
                                 stdout=f,
                                 stderr=f
                                 )

        if verbose:
            with open(logfile, 'r') as f: print(f.read())

        if rc == 0:
            return True
        else:
            print('! ERROR: Execution ended with error code '+str(rc)+'!\n! Please check log file in')
            print('! '+logfile)
            return rc


    def clear_src(self, do_it=False, do_it_really=False):
        """ This method clears the src directory of the simulation!
        All files in src get deleted, except of whats in components and optionals!
        By default, everything except Makefile.local and cparam.local gets erased!

        Args:
            to activate pass        True, True
        """
        from os import listdir
        from os.path import join, exists
        from pencilnew.io import remove_files as remove

        folder = join(self.path,'src')
        keeps = [f.split('/')[-1] for f in self.components+self.optionals]

        if not exists(folder): print('? Warning: No src directory found!'); return True

        filelist = listdir(folder)          # remove everything INSIDE
        for f in filelist:
            if f in keeps: continue
            remove(join(folder,f), do_it=do_it, do_it_really=do_it_really)
        return True


    def clear_data(self, do_it=False, do_it_really=False):
        """ This method clears the data directory of the simulation!
        All files in data get deleted!

        Args:
            to activate pass        True, True
        """
        from os import listdir
        from os.path import join, exists
        from pencilnew.io import remove_files as remove

        folder = join(self.path,'data')
        keeps = []

        if not exists(folder): print('? Warning: No data directory found!'); return True

        filelist = listdir(folder)          # remove everything INSIDE
        for f in filelist:
            if f in keeps: continue
            remove(join(folder,f), do_it=do_it, do_it_really=do_it_really)
        return True


    def remove(self, do_it=False, do_it_really=False, remove_data=False):
        """ This method removes the WHOLE simulation,
        but NOT the DATA directory per default.
        Do remove_data=True to delete data dir as well.

        Args:
            to activate pass        True, True
            remove_data:            also clear data directory
        """
        from os import listdir
        from os.path import join
        from pencilnew.io import remove_files as remove

        self.clear_src(do_it=do_it, do_it_really=do_it_really)
        if remove_data:
            self.clear_data(do_it=do_it, do_it_really=do_it_really)

        filelist = listdir(self.path)
        for f in filelist:
            remove(join(self.path, f), do_it=do_it, do_it_really=do_it_really)
        return True


    def get_varlist(self, pos=False, particle=False):
        """Get a list of all existing VAR# file names.

        pos = False:                 give full list
        pos = 'last'/'first':        give latest/first var file
        pos = 'lastXXX' / 'firstXXX' give last/first XXX varfiles
        pos = list of numbers:       give varfiles at this positions
        particle = True:             return PVAR- instead of VAR-list"""

        import glob
        from os.path import join as join
        from os.path import basename
        from pencilnew.math import natural_sort

        key = 'VAR'
        if particle == True: key = 'PVAR'

        varlist = natural_sort([basename(i) for i in glob.glob(join(self.datadir, 'proc0')+'/'+key+'*')])
        #if particle: varlist = ['P'+i for i in varlist]

        if pos == False: return varlist
        if pos == 'first': return [varlist[0]]
        if pos == 'last': return [varlist[-1]]
        if pos.startswith('last'): return varlist[-int(pos[4:]):]
        if pos.startswith('first'): return varlist[:int(pos[4:])]
        if type(pos) == type([]):
            if pos[0].startswith('VAR'): pos = [i[3:] for i in pos]
            if pos[0].startswith('PVAR'): pos = [i[3:] for i in pos]
            return [varlist[int(i)] for i in pos]
        return varlist


    def get_pvarlist(self, pos=False):
        """Same as get_varfiles(pos, particles=True). """
        return self.get_varfiles(pos=pos, particle=True)


    def get_lastvarfilename(self, particle=False):
        """Returns las varfile name as string."""
        return self.get_varfiles(pos='last', particle=particle)


    def get_value(self, quantity, DEBUG=False):
        """Optimized version of get_value_from_file. Just state quantity for simulation and param-list together with searchable components will be searched."""

        if DEBUG: print('~ DEBUG: Updating simulation.')
        self.update()

        if DEBUG: print('~ DEBUG: Searching through simulation.params ...')
        if type(self.param) == type({'dictionary': 'with_values'}):
            if quantity in self.param.keys():
                if DEBUG: print('~ DEBUG: '+quantity+' found in simulation.params ...')
                return self.param[quantity]

        if DEBUG:
            print('~ DEBUG: Searching through simulation.quantity_searchables ...')
        from pencilnew.io import get_value_from_file
        for filename in self.quantity_searchables:
            q = get_value_from_file(filename, quantity, change_quantity_to=False,
                                    sim=self, DEBUG=DEBUG, silent=True)
            if q is not None:
                if DEBUG: print('~ DEBUG: '+quantity+' found in '+filename+' ...')
                return q

        print('! ERROR: Couldnt find '+quantity+'!')

    def get_ts(self):
        """Returns time series object."""
        from pcn.read import ts
        if self.started():
            return ts(sim=self, quiet=True)
        else:
            print('? WARNING: Simulation '+self.name+' has not yet been started. No timeseries available!')
            return False

    def change_value_in_file(self, filename, quantity, newValue, filepath=False, DEBUG=False):
        """Same as pencilnew.io.change_value_in_file."""
        from pencilnew.io import change_value_in_file

        return change_value_in_file(filename, quantity, newValue, sim=self, filepath=filepath, DEBUG=DEBUG)
