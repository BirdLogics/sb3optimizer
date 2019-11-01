# sb3 optimizer
# Version 0.0.1

import argparse, logging
import json, zipfile
import itertools
import os, sys
import shutil

UIDCHARS = "!#%()*+,-./:;=?@[]^_`{|}~ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"

# Configure the logger
logging.basicConfig(format="%(levelname)s: %(message)s", level=10)
log = logging.getLogger()

def main():
    # Get the object to handle the sb3 file
    sbf = sb3file("project.sb3", True, True)

    # Load the sb3 project json
    sb3 = sbf.readsb3()

    # Make sure everything loaded correctly
    if sb3:
        log.info("Optimizing block uids...")
        OptimizeBlockUIDs(sb3)

        log.info("Removing monitors...")
        RemoveMonitors(sb3, True)

        log.info("Optimizing variable/list uids...")
        OptimizeVariableUIDs(sb3)

        # Save the new sb3
        log.info("Saving results...")
        if not sbf.savesb3("result.sb3.zip", sb3):
            log.critical("Failed to save the sb3 project.")
    else:
        log.critical("Failed to load the sb3 project.")

# Gets a small, unique uid
def GetUID(chars):
    r = 1 # Number of character that make up the uid
    while True:
        for c in itertools.combinations_with_replacement(chars, r):
            yield c
        r += 1

def GetBlocks(sb3):
    for target in sb3["targets"]:
        for block in target["blocks"].items():
            yield block

# Replace uids with shortened versions
def OptimizeBlockUIDs(sb3):
    uids = {} # Holds uids and their usage
    blocks = [] # Holds every block in the project
    new_uids = {} # Holds the new uids

    log.debug("Counting block uids...")

    # Initialize with the uids for each block
    for target in sb3["targets"]:
        for uid, block in target["blocks"].items():
            uids[uid] = []
            blocks.append(block)
    
    # Count each uid's usage
    for block in blocks:
        # Check that it is a normal block
        if type(block) == dict:
            # Add uids to the list
            if "parent" in block and block["parent"]:
                uids[block["parent"]].append(("parent", block))
            if "next" in block and block["next"]:
                uids[block["next"]].append(("next", block))

            # Find uids in the inputs
            for value in block["inputs"].values():
                # Wrapper; block or value
                if value[0] == 1:
                    # Block if value[1][0] is 2
                    if type(value[1]) == list:
                        value = value[1]
                    # It's a block
                    elif value[1]:
                        uids[value[1]].append((1, value))
                
                # Block covering a value
                elif value[0] == 3 and type(value[1]) == str:
                    uids[value[1]].append((1, value))
                
                # It's a block
                if value[0] == 2 and type(value[1]) == str:
                    uids[value[1]].append((1, value))

    log.debug("Assigning block uids...")
    
    # Sort the uids based on frequency
    freq = sorted(uids.items(), key=lambda d: len(d[1]), reverse=True)

    # Assign new ids starting with shorter ones
    for old, new in zip(freq, GetUID(UIDCHARS)):
        new_uids[old[0]] = ''.join(new)

    log.debug("Replacing block uids...")

    # Replace the old ids with new ones
    for target in sb3["targets"]:
        for uid in tuple(target["blocks"]):
            target["blocks"][new_uids[uid]] = target["blocks"].pop(uid)

    # Replace uses of the olds ids
    for uid, usages in uids.items():
            for key, container in usages:
                container[key] = new_uids[uid]

def RemoveMonitors(sb3, removeVisible=False):
    if removeVisible:
        sb3["monitors"] = []
    else:
        log.warning("Visible monitor exclusion not tested.")
        for monitor in sb3["monitors"]:
            if not monitor["visible"]:
                del monitor

def OptimizeVariableUIDs(sb3):
    """Optimizes the uids for variable and lists"""
    uids = {} # Holds uids and their usage
    new_uids = {} # Holds the new uids

    log.debug("Counting variable uids...")

    # Initialize with the uids for each variable/list
    for target in sb3["targets"]:
        for uid in target["variables"].keys():
            uids[uid] = []
        for uid in target["lists"].keys():
            uids[uid] = []
    
    # Count each uid's usage
    for target in sb3["targets"]:
        for block in target["blocks"].values():
            # Check to see if it is a block or variable
            if type(block) == dict:
                # Find uids in the inputs
                for value in block["inputs"].values():
                    # Wrapper; block or value
                    if value[0] == 1 and type(value[1]) == list:
                        value = value[1]
                    # Block or variable/list
                    elif value[0] == 3 and type(value[1]) == list:
                        value = value[1]
                    # Block or variable/list
                    if value[0] == 2 and type(value[1]) == list:
                        value = value[1]
                    
                    # Variable
                    if value[0] == 12:
                        uids[value[2]].append((2, value))
                    elif value[0] == 13:
                        uids[value[2]].append((2, value))
                
                if "VARIABLE" in block["fields"]:
                    uids[block["fields"]["VARIABLE"][1]].append((1, block["fields"]["VARIABLE"]))
                elif "LIST" in block["fields"]:
                    uids[block["fields"]["LIST"][1]].append((1, block["fields"]["LIST"]))
            else:
                log.warning("Unused variable reporters not tested.")
                if block[0] == 12:
                    uids[block[2]].apppend((2, value))
                elif block[0] == 13:
                    uids[block[2]].append((2, value))
            

    log.debug("Assigning variable uids...")
    
    # Sort the uids based on frequency
    freq = sorted(uids.items(), key=lambda d: len(d[1]), reverse=True)

    # Assign new ids starting with shorter ones
    for old, new in zip(freq, GetUID(UIDCHARS)):
        new_uids[old[0]] = ''.join(new)

    log.debug("Replacing variable uids...")

    # Replace the old ids with new ones
    for target in sb3["targets"]:
        for uid in tuple(target["variables"]):
            target["variables"][new_uids[uid]] = target["variables"].pop(uid)
        for uid in tuple(target["lists"]):
            target["lists"][new_uids[uid]] = target["lists"].pop(uid)

    # Replace uses of the olds ids
    for uid, usages in uids.items():
        for key, container in usages:
            container[key] = new_uids[uid]

class sb3file:
    sb3_file = None # Holds the sb3 file
    sb3_path = None # Holds the path to the sb3 file

    json_path = "project.json" # Holds the path to the json

    overwrite = False # Whether files may be overwritten
    debug = False # Whether to save a debug json

    def __init__(self, sb3_path, overwrite=False, debug=False):
        self.sb3_path = sb3_path
        if not os.path.isfile(sb3_path):
            log.warning("File %s does not exist." %sb3_path)

        self.overwrite = overwrite
        self.debug = debug
    
    def readsb3(self):
        sb3_file = None

        try:
            # Open the sb3 file
            sb3_file = zipfile.ZipFile(self.sb3_path, "r")

            # Find the sb3 json path
            ext = self.sb3_path.split(".")[-1]
            files = sb3_file.namelist()
            if ext == "sb3":
                self.json_path = "project.json"
                if not "project.json" in files and "sprite.json" in files:
                    self.json_path = "sprite.json"
                    log.warning("File '%s' has a sb3 extension but appears to be a sprite.", sb3_path)
            elif ext == "sprite3":
                self.json_path = "sprite.json"
                if not "sprite.json" in files and "project.json" in files:
                    self.json_path = "project.json"
                    log.warning("File '%s' has a sprite3 extension but appears to be a project.", sb3_path)
            else:
                self.json_path = "project.json"
                if not "project.json" in files and "sprite.json" in files:
                    self.json_path = "sprite.json"
            
            # Read and parse the json
            sb3_json = sb3_file.read(self.json_path)
            sb3 = json.loads(sb3_json)

            return sb3

        # Handle errors cleanly
        except FileNotFoundError:
            log.warning("File '%s' not found.", self.sb3_path)
        except zipfile.BadZipFile:
            log.warning("File '%s' is not a valid zip file.", self.sb3_path)
        except KeyError:
            log.warning("Failed to find json '%s' in '%s'.", self.json_path, self.sb3_path)
        except json.decoder.JSONDecodeError:
            log.warning("File '%s/%s' is not a valid json file.", self.sb3_path, self.json_path)
        except:
            log.error("Unkown error reading '%s'.", self.sb3_path, exc_info=True)
        finally:
            if sb3_file: sb3_file.close()

        return False

    def savesb3(self, save_path, sb3, prettyDebug=True):
        # Initialize variables which hold file objects
        sb3_old = None
        sb3_file = None
        sb3_jfile = None
        
        try:
            # Get the sb3 json string
            sb3_json = json.dumps(sb3)

            # Save a debug json
            if self.debug and self.overwrite:
                # Get a prettified debug json
                if prettyDebug:
                    log.debug("Prettifying debug json...")
                    debug_json = json.dumps(sb3, indent=4, separators=(',', ': '))
                else:
                    debug_json = sb3_json
                
                # Save a copy of the json
                sb3_jfile = open(self.json_path, "w")
                sb3_jfile.write(debug_json)
                log.info("Saved debug to '%s'.", self.json_path)

            if self.sb3_path == save_path:
                log.error("Save path cannot be the same as the read path.")
                return False
            
            log.debug("Saving to '%s'...", save_path)

            # Open the old sb3 so it can be copied
            sb3_old = zipfile.ZipFile(self.sb3_path, "r")

            # Create the new sb3 file
            if self.overwrite:
                sb3_file = zipfile.ZipFile(save_path, "w", compression=zipfile.ZIP_DEFLATED)
            else:
                sb3_file = zipfile.ZipFile(save_path, "x", compression=zipfile.ZIP_DEFLATED)
            
            # Copy the the old sb3
            for info in sb3_old.infolist():
                if info.filename != self.json_path:
                    sb3_file.writestr(info, sb3_old.read(info.filename))
            
            # Save the sb3 json
            sb3_file.writestr(self.json_path, sb3_json)

            log.info("Saved to '%s'", save_path)

            return True
        
        # Handle errors
        except FileNotFoundError:
            log.warning("File '%s' not found.", self.sb3_path)
        except zipfile.BadZipFile:
            log.warning("File '%s' is not a valid zip file.", self.sb3_path)
        except FileExistsError:
            log.warning("File '%s' already exists. Delete or rename it and try again.", save_path)
        except:
            log.error("Unkown error saving to '%s' or reading from '%s'.", save_path, self.sb3_path, exc_info=True)
        finally:
            if sb3_old: sb3_old.close()
            if sb3_file: sb3_file.close()
            if sb3_jfile: sb3_jfile.close()
            elif self.debug: log.warning("Did not save debug json to '%s'." % self.json_path)
       
        return False

if __name__ == "__main__":
    main()