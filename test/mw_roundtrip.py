import bpy
import addon_utils

import os
import sys

import traceback

import resource

from pyffi.formats.nif import NifFormat

def allNifs(baseDirectory):
    nifs = []
    for root, dirs, files in os.walk(baseDirectory):
        for file in files:
            if file.endswith(".nif"):
                nifs.append(os.path.join(root, file))

    print("Found {0} files".format(len(nifs)))
    return sorted(nifs, key=lambda file: (os.path.dirname(file), os.path.basename(file)))

def loadAddon():
    expectedAddonName = "NetImmerse/Gamebryo nif format"
    expectedAddonVersion = (2, 6, 0)

    addonFound = False

    for mod in addon_utils.modules():
        if mod.bl_info['name'] == expectedAddonName:
            version = mod.bl_info['version']
            if version == expectedAddonVersion:
                addonFound = True
            else:
                raise Exception("Unexpected addon version: " + str(version))

    if not addonFound:
        raise Exception("Addon not found")

    print("Enabling addon")
    addon_utils.enable("io_scene_nif", default_set=True, persistent=False, handle_error=None)
    print(bpy.context.user_preferences.addons.keys())

# ======================================================================================================================

def niffdiff(importFile, exportFile):
    imported = NifFormat.Data()
    with open(importFile, "rb") as stream:
        imported.read(stream)

    exported = NifFormat.Data()
    with open(exportFile, "rb") as stream:
        exported.read(stream)

    if imported.version != exported.version:
        raise RuntimeError("Version mismatch {0} {1}".format(imported.version, exported.version))


    if len(imported.roots) != len(exported.roots):
        raise RuntimeError("Roots size mismatch")

    for ir, er in zip(imported.roots, exported.roots):
        if(ir != er):
            raise RuntimeError("Roots mismatch")

    if imported.blocks != exported.blocks:
        raise RuntimeError("Blocks mismatch")

# ======================================================================================================================

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Please supply directory path to unpacked bsa data")
        exit()

    baseDirectory = sys.argv[1]
    #problemFiles = [baseDirectory+"/meshes/base_anim_female.1st.nif"]
    problemFiles = [baseDirectory+"/meshes/a/a_art_apostle_boots_gnd.nif"]
    problemFiles = [baseDirectory+"/meshes/a/a_art_cuirass_lords_c.nif"]
    problemFiles = [baseDirectory+"/meshes/a/a_art_cuirass_savior_c.nif"]

    loadAddon()

    nifFiles = problemFiles
    nifFiles = allNifs(baseDirectory + "/meshes")

    statusFile = open("test_files.txt", "w")
    exceptionsFile = open("test_exceptions.txt", "w")

    exceptionId = 0

    statusColumnWidth = 15

    statusFile.write("Import".ljust(statusColumnWidth) + "\t" + "Export".ljust(statusColumnWidth) + "\t" + "Compare".ljust(statusColumnWidth) + "\t" + "File\n")

    for originalNifFile in nifFiles:
        bpy.ops.wm.read_homefile()
        relFile = os.path.relpath(originalNifFile, baseDirectory)

        exportFilePath = "test.nif"

        try:
            bpy.ops.import_scene.nif(log_level='DEBUG', animation=False, filepath = originalNifFile)
            importStatus = "Ok"
            importOk = True
        except RuntimeError as e:
            importOk = False
            exceptionsFile.write("Exception {0}\n".format(exceptionId))
            exceptionsFile.write(e.args[0])
            exceptionsFile.flush()
            importStatus = "Failed {0:04d}".format(exceptionId)
            exceptionId += 1
            #traceback.print_exc(file=resultFile)

        if importOk:
            try:
                bpy.ops.export_scene.nif(log_level='DEBUG', game='MORROWIND', filepath=exportFilePath)
                exportStatus = "Ok"
                exportOk = True
            except RuntimeError as e:
                exportOk = False
                exceptionsFile.write("Exception {0}\n".format(exceptionId))
                exceptionsFile.write(e.args[0])
                exceptionsFile.flush()
                exportStatus = "Failed {0:04d}".format(exceptionId)
                exceptionId += 1
        else:
            exportStatus = "Skip"

        if False and importOk and exportOk:
            try:
                niffdiff(originalNifFile, exportFilePath)
                compareStatus = "Ok"
            except RuntimeError as e:
                exceptionsFile.write("Exception {0}\n".format(exceptionId))
                exceptionsFile.write(e.args[0])
                exceptionsFile.flush()
                compareStatus = "Failed {0:04d}".format(exceptionId)
                exceptionId += 1
        else:
            compareStatus = "Skip"

        statusFile.write(importStatus.ljust(statusColumnWidth) + "\t" + exportStatus.ljust(statusColumnWidth) + "\t" + compareStatus.ljust(statusColumnWidth) + "\t" + str(relFile) + "\n")
        statusFile.flush()

    statusFile.close()
