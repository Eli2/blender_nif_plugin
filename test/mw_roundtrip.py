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

def nifdiff_NiNode(expected, actual):
    errors = []

    if not isinstance(expected, actual.__class__):
        errors.append("type mismatch expected {0} actual {1}".format(type(expected), type(actual)))
        return errors

    if isinstance(expected, NifFormat.NiTexturingProperty):
        pass
    elif isinstance(expected, NifFormat.NiSourceTexture):
        pass
    elif isinstance(expected, NifFormat.NiMaterialProperty):
        pass
    elif isinstance(expected, NifFormat.NiTriShape):
        pass
    elif isinstance(expected, NifFormat.NiTriShapeData):
        pass
    elif isinstance(expected, NifFormat.NiSkinInstance):
        pass
    elif isinstance(expected, NifFormat.NiSkinData):
        pass
    else:
        if not expected.name == actual.name:
            errors.append("name mismatch expected {0} actual {1}".format(expected.name, actual.name))

        if not expected.has_bounding_box == actual.has_bounding_box:
            errors.append("has_bounding_box mismatch expected {0} actual {1}".format(expected.has_bounding_box, actual.has_bounding_box))

        if expected.has_bounding_box:
            if not expected.bounding_box == actual.bounding_box:
                errors.append("bounding_box mismatch expected {0} actual {1}".format(expected.bounding_box, actual.bounding_box))

        if not expected.flags == actual.flags:
            errors.append("flags mismatch expected {0} actual {1}".format(expected.flags, actual.flags))

        if not expected.translation == actual.translation:
            errors.append("translation mismatch expected {0} actual {1}".format(expected.translation, actual.translation))

        if not expected.rotation == actual.rotation:
            errors.append("rotation mismatch expected {0} actual {1}".format(expected.rotation, actual.rotation))

        if not expected.scale == actual.scale:
            errors.append("scale mismatch expected {0} actual {1}".format(expected.scale, actual.scale))

        if not expected.velocity == actual.velocity:
            errors.append("scale mismatch expected {0} actual {1}".format(expected.scale, actual.scale))

    if isinstance(expected, NifFormat.NiTriShape):
        print("foo")

    return errors

def niffdiff(importFile, exportFile):
    errors = []

    expected = NifFormat.Data()
    with open(importFile, "rb") as stream:
        expected.read(stream)

    actual = NifFormat.Data()
    with open(exportFile, "rb") as stream:
        actual.read(stream)

    if expected.version != actual.version:
        errors.append("Version mismatch {0} actual {1}".format(expected.version, actual.version))

    if len(expected.roots) != len(actual.roots):
        errors.append("roots size mismatch expected {0} actual {1}".format(len(expected.roots), len(actual.roots)))

    for ir, er in zip(expected.roots, actual.roots):
        errors.extend(nifdiff_NiNode(ir, er))

    if not len(expected.blocks) == len(actual.blocks):
        errors.append("blocks size mismatch {0} actual {1}".format(len(expected.blocks), len(actual.blocks)))

    for ir, er in zip(expected.blocks, actual.blocks):
        errors.extend(nifdiff_NiNode(ir, er))

    return errors

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
    nifFiles = allNifs(baseDirectory + "/meshes/a")

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

        if importOk and exportOk:
            diffErrors = niffdiff(originalNifFile, exportFilePath)
            if len(diffErrors) == 0:
                compareStatus = "Ok"
            else:
                exceptionsFile.write("Error: {0}\n".format(exceptionId))
                for error in diffErrors:
                    exceptionsFile.write("%s\n" % error)
                exceptionsFile.flush()
                compareStatus = "Failed {0:04d}".format(exceptionId)
                exceptionId += 1
        else:
            compareStatus = "Skip"

        statusFile.write(importStatus.ljust(statusColumnWidth) + "\t" + exportStatus.ljust(statusColumnWidth) + "\t" + compareStatus.ljust(statusColumnWidth) + "\t" + str(relFile) + "\n")
        statusFile.flush()

    statusFile.close()
