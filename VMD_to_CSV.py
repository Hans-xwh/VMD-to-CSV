import ast
import csv
import pathlib
import struct
import sys
import time         #only for timer
import tkinter
import tkinter.filedialog     #for testing

delimiter = ','     #delimiter for the csv. Can be anything i think.
encoding = 'utf-8'  #encoding fo the otput CSV. VMD will always use 'shift-jis'. Use something that supports japanese characters.

#Declaring variables, just like we're in c# (for testing only, might remove later)
boneKeyCount, faceKeyCount, camKeyCount, faceBytePos, camBytePos = [int(),int(),int(),int(),int()]
magiString, modelName = str(), str()
excessData  = bytes()
vmd_wr = bytearray()
blocksWritten = 1

startTime = time.time()

class Bone:                                                                                     #Not really sure what i'm doing but this works lol
    def __init__(bone, interation, name, frame, posX, posY, posZ, rotX, rotY, rotZ, rotW, curve): #Curve is 64 bytes
        bone.iteration = int()
        bone.name = str()
        bone.frame = int()    #starts to count from 0
        bone.posX = float()
        bone.posY = float()
        bone.posZ = float()
        bone.rotX = float()
        bone.rotY = float()
        bone.rotZ = float()
        bone.rotW = float()
        bone.curve = bytes()


class Face:
    def __init__(face, iteration, name, frame, weight):
        face.iteration = int()
        face.name = str()
        face.frame = int()    #starts from 0
        face.weight = float() # *Should* go from 0 to 1


class Cam:
    def __init__(cam, interation, frame, distance, posX, posY, posZ, rotX, rotY, rotZ, fov, per, curve): #Note: Curve is 24 bytes.
        cam.iteration = int()
        cam.frame = int()
        cam.distance = float()
        cam.posX = float()
        cam.posY = float()
        cam.posZ = float()
        cam.rotX = float()
        cam.rotY = float()
        cam.rotZ = float()
        cam.fov = int()
        cam.per = int()      #Not really sure if this should be bool or int.
        cam.curve = bytes()


def readVmd(file):
    with open(file, mode="rb") as sourceVmd:                                                    
        vmd_bin = sourceVmd.read()                                                              #Load the source vmd file. 'With' will close the file when finished.
        #print("File read done")

        if vmd_bin[:25].decode('shift-jis') != 'Vocaloid Motion Data 0002' and vmd_bin[:25].decode('shift-jis') != 'Vocaloid Motion Data file': #Check if the file has a valid header. To disable this check, comment out the if statement.
            exit('Header error: This is not a proper vmd!')                                     #Exit if header is invalid.

    return bytes(vmd_bin)


def writeVmd(output_path, data):
    with open(output_path, mode="wb") as outVmd:
        outVmd.write(data)                                                                      #Write the input binary data as vmd file.
        #print("File Write done")
    return


def decodeStart(data=bytes()):
    #print(len(data))
    # Header

    excessData = bytes
    magiString = data[:30].decode('shift-jis')                                                  #Decode and save the full magic string.
    magiString = magiString.replace('\x00','')                                                  #Removes blanks.
    modelName = data[30:50].decode('shift-jis')                                                 #Decode the model name (also used as motion name)
    modelName = modelName.replace('\x00','')

    boneKeyCount = int.from_bytes(data[50:53], byteorder='little')                              #Decode the number bone keyframes.
    FaceBytePos = (1 + 53 + (boneKeyCount * 111))                                               #Set next read position
    print('Bone Keyframes: ' + str(boneKeyCount)) #debug
    #print('nextStartPos is: ' + str(FaceBytePos)) #debug


    faceKeyCount = int.from_bytes(data[FaceBytePos:(FaceBytePos+3)], byteorder='little')        #Decode number of facial keyframes.
    CamBytePos = (4 + FaceBytePos + (faceKeyCount * 23))                                        #Set next read position
    print('Face Keyframes: ' + str(faceKeyCount)) #debug
    #print('nextStartPos is: ' + str(CamBytePos)) #debug


    camKeyCount = int.from_bytes(data[CamBytePos:(CamBytePos+3)], byteorder='little')           #Decode number of facial keyframes.
    nextPos = (15 +CamBytePos + (camKeyCount * 61))                                             #Set end of reading position. There "should" be 16 null bytes at the end of the file.
    print('Camera Keyframes: ' + str(camKeyCount)) #debug
    #print('final byte offset is: ' + str(nextPos)) #debug

    if len(data) != nextPos:                                                                    #Check if there is data after the parsed block. There sometimes is, as vmd can also store properties. This script does not conver those, so they just saved for later reconstruction.
        #print('Warning, there is data after standard animation block!')
        excessData = (data[nextPos:])                                                           #Save the excess data.
        nextPos = (nextPos + len(excessData))                                                   #Set position after the excess data block. This should alwas match the end of the file.

    #print(magiString)
    #print(modelName)
    #print(boneKeyCount)
    #print(faceKeyCount)
    #print(camKeyCount)

    #if len(data) == nextPos:
    #    print('Seems to be Ok!')
    #else:
    #    print('Somethign went terribly wrong...')


    return magiString, modelName, boneKeyCount, faceKeyCount, camKeyCount, FaceBytePos, CamBytePos, excessData


def decodeBones(data=bytes, i=int): #i (iterations) starts to count from zero! #start to decode at byte 54. Maybe use smth like nextPos to avoid doing to much math.
    startByte = 54 + (i * 111)      #startByte will be the first byte to be read on each block operation. the variable i is used to offset this each operation.

    Bone.iteration = i              #Write the current iteration as part of the Bone object. This is not part of the vmd, but this is will be usefull to convert from text format back to vmd.

    Bone.name = data[startByte:startByte + 15].decode('shift-jis', errors= 'strict')
    Bone.name = Bone.name.replace('\x00','')
    startByte += 15

    Bone.frame = int.from_bytes(data[startByte: startByte + 4], byteorder='little')             #quite intuitive what's happening here. Decode the bytes in the correct format,
    startByte += 4                                                                              #then offset the startByte by the length of the processed block for the next decode operation.

    Bone.posX = struct.unpack('f', data[startByte: startByte + 4])                      
    startByte += 4

    Bone.posY = struct.unpack('f', data[startByte: startByte + 4])
    startByte += 4

    Bone.posZ = struct.unpack('f', data[startByte: startByte + 4])
    startByte += 4

    Bone.rotX = struct.unpack('f', data[startByte: startByte + 4])
    startByte += 4

    Bone.rotY = struct.unpack('f', data[startByte: startByte + 4])
    startByte += 4

    Bone.rotZ = struct.unpack('f', data[startByte: startByte + 4])
    startByte += 4

    Bone.rotW = struct.unpack('f', data[startByte: startByte + 4])
    startByte += 4

    Bone.curve = data[startByte: startByte + 64]

    #print('Bone number', Bone.iteration)
    #print('Bone name:', Bone.name)
    #print('Bone frame:', Bone.frame)
    #print('Bone Position X:', Bone.posX)
    #print('Bone Position Y:', Bone.posY)
    #print('Bone Position Z:', Bone.posZ)
    #print('Bone Rotation X:', Bone.rotX)
    #print('Bone Rotation Y:', Bone.rotY)
    #print('Bone Rotation Z:', Bone.rotZ)
    #print('Bone Rotation W:', Bone.rotW)

    return(Bone)


def decodeFace(data=bytes, i=int):
    startByte = faceBytePos + 4
    startByte = startByte + (23 * i)                                                            #Same here, offset each start possition by the lenght of the data blocks.

    Face.iteration = i

    Face.name = data[startByte:startByte + 15].decode('shift-jis', errors='replace')            #This will be losy if the morph name has invalid character. I wanted so bad to make this as looseless as possible T_T
    Face.name = Face.name.replace('\x00','')
    startByte += 15

    Face.frame = int.from_bytes(data[startByte: startByte + 4], byteorder='little')
    startByte += 4

    Face.weight = struct.unpack('f', data[startByte: startByte + 4])

    #print('Face name: ', Face.name)
    #print('Face frame: ', Face.frame)
    #print('Face wiight: ', Face.weight)

    return(Face)


def decodeCamera(data, i=int):

    startByte = camBytePos
    startByte = startByte + 4 + (61 * i)   

    Cam.iteration = i

    Cam.frame = int.from_bytes(data[startByte: startByte + 4], byteorder='little')
    startByte += 4

    Cam.distance = struct.unpack('f', data[startByte: startByte + 4])
    startByte += 4

    Cam.posX = struct.unpack('f', data[startByte: startByte + 4])
    startByte += 4

    Cam.posY = struct.unpack('f', data[startByte: startByte + 4])
    startByte += 4

    Cam.posZ = struct.unpack('f', data[startByte: startByte + 4])
    startByte += 4

    Cam.rotX = struct.unpack('f', data[startByte: startByte + 4])
    startByte += 4

    Cam.rotY = struct.unpack('f', data[startByte: startByte + 4])
    startByte += 4

    Cam.rotZ = struct.unpack('f', data[startByte: startByte + 4])
    startByte += 4

    Cam.curve = data[startByte: startByte + 24]
    startByte += 24

    Cam.fov = int.from_bytes(data[startByte: startByte + 4], byteorder= 'little')
    startByte += 4

    Cam.per = int.from_bytes(data[startByte: startByte + 1], byteorder='little')

    #print('Camera frame:', Cam.frame)
    #print('Camera distance:', Cam.distance)
    #print('Camera Position (X):', Cam.posX)
    #print('Camera Position (Y):', Cam.posY)
    #print('Camera Position (Z):', Cam.posZ)
    #print('Camera Rotation (X):', Cam.rotX)
    #print('Camera Rotation (Y):', Cam.rotY)
    #print('Camera Rotation (Z):', Cam.rotZ)
    #print('Camera FOV:', Cam.fov)
    #print('Camera Perspective:', Cam.per)

    return(Cam)


def WriteBones(Bone=Bone):      #Unused. For testing only.
    #print('Bone name:', Bone.name)
    row = [Bone.iteration, Bone.name, Bone.frame, Bone.posX, Bone.posY, Bone.posZ, Bone.rotX, Bone.rotY, Bone.rotZ, Bone.rotW, Bone.curve]

    with open(OutCsv,'a', encoding = encoding, newline= '') as csvFile:
        writer = csv.writer(csvFile)
        writer.writerow(row)

    return

def writeCsv(out):                      #This is the main function to convert VMD -> Csv. This calls everything else, except for the header. That sould be run first.
    #Header writing
    with open(out, '+a', encoding= encoding, newline= '') as csvFile:
        firstRow = ['Motion Name', 'Bone keys', 'Face keys', 'Camera keys']
        headerRow = [modelName, boneKeyCount, faceKeyCount, camKeyCount]

        writer = csv.writer(csvFile)
        writer.writerow(firstRow)
        writer.writerow(headerRow)

        pass


    #Bone csv data writing
    if boneKeyCount > 0:
        with open(out, '+a', encoding= encoding, newline= '') as csvFile:
            BoneRow = ['Iteration', 'Name', 'Frame', 'Positon (X)', 'Positon (Y)', 'Positon (Z)', 'Rotation (X)', 'Rotation (Y)', 'Rotation (Z)', 'Rotation (W)', 'Intrapolation']

            writer = csv.writer(csvFile)
            writer.writerow(['#---Bone Data---'])
            writer.writerow(BoneRow)

            print('Working on bone data...')

            i = 0
            while i < boneKeyCount:
                #WriteBones(decodeBones(vmd_bin, i)) #Spagetti code, i know. But it works.

                Bone = decodeBones(vmd_bin, i)
                #print('Bone name:', Bone.name)
                row = [Bone.iteration, Bone.name, Bone.frame, Bone.posX, Bone.posY, Bone.posZ, Bone.rotX, Bone.rotY, Bone.rotZ, Bone.rotW, Bone.curve]
                writer = csv.writer(csvFile)
                writer.writerow(row)
                i += 1
        print('Finished writing Bones')
    #else:
        #print('No bone data!')

    #Facial csv data writing
    if faceKeyCount > 0:
        with open(out, '+a', encoding = encoding, newline= '') as csvFile:                                 #Open the file again and write the face data block.
            faceRow = ['Iteration', 'Morph Name', 'Frame', 'Weight']
            writer = csv.writer(csvFile)
            writer.writerow(['#---Face Data---'])
            writer.writerow(faceRow)

            print('Working on morph data...')
            i = 0
            while i < faceKeyCount:
                #print('Current iteration:', i)
                Face = decodeFace(vmd_bin,i)
                row = [Face.iteration, Face.name, Face.frame, Face.weight]

                writer.writerow(row)

                i += 1
        print('Finished writing Morphs')
    #else:
        #print('No facial data!')
        
    #Cam csv data writing
    if camKeyCount > 0:
        with open(out, '+a', encoding=encoding, newline= '') as csvFile:
            camRow = ['Iteration', 'Frame', 'Distance', 'Position (X)', 'Position (Y)', 'Position (Z)', 'Rotation (X)', 'Rotation (Y)', 'Rotation (Z)', 'FOV', 'Orthographic', 'Intrapolation']
            writer = csv.writer(csvFile)
            writer.writerow(['#Camera Data'])
            writer.writerow(camRow)

            print('Working on camera data...')
            i = 0
            while i < camKeyCount:
                #print('Current Cam Iteration:', i)
                Cam = decodeCamera(vmd_bin, i)
                row = [Cam.iteration, Cam.frame, Cam.distance, Cam.posX, Cam.posY, Cam.posZ, Cam.rotX, Cam.rotY, Cam.rotZ, Cam.fov, Cam.per, Cam.curve]

                writer.writerow(row)
                i += 1
        print('Finished writing Camera')
    #else:
       #print('No Camera data!')


def encodeHeader(modelName = str, boneKeyCount = int, faceKeyCount = int, camKeyCount = int):

    global vmd_bin
    global vmd_wr
    global blocksWritten
    blocksWritten = 1

#   --- Encode the file header and the model/motion name ---
    vmd_wr = 'Vocaloid Motion Data 0002'.encode(encoding='shift-jis')
    vmd_wr += bytes(b'\x00\x00\x00\x00\x00')                           #Add some blank byte so file header is 30 bytes long
    modelBin = modelName.encode(encoding='shift-jis')

    if modelBin == bytes(b'\x83\x4a\x83\x81\x83\x89\x81\x45\x8f\xc6\x96\xbe\x6f\x6e\x20\x44\x61\x74\x61'):
        modelBin = bytes(b'\x83\x4a\x83\x81\x83\x89\x81\x45\x8f\xc6\x96\xbe\x00\x6f\x6e\x20\x44\x61\x74\x61') #Correct model name to camera motion indicator. Otherwise mmd will refuse to load the resulting file.
        print('Working with a cam/light/shadow vmd')

    vmd_wr += modelBin
    #print(modelBin)

    t= 20 - len(modelBin)
    i= 0
    while i < t:
        vmd_wr += bytes(b'\x00')
        i += 1
        #print('Added one Byte')
    #print(vmd_wr)
    if len(modelBin) > 20:
        print('Fatal error, Model Name is too long!')
        exit()                                              #Maybe there is no need to stop this way?

#   --- Encode amount of bone data blocks ---
    vmd_wr += boneKeyCount.to_bytes(4, byteorder='little')

    print('Header written')
    #print(vmd_wr)

    with open(OutputVMD, mode="wb") as outVmd:
        outVmd.write(vmd_wr)                                                                      #Write the input binary data as vmd file.
        #print("File Write")
    
    return vmd_wr,


def encodeBones(Bone=Bone,):
#   --- Encode Bone name & check the byte lenght ---
    vmd_wr = Bone.name.encode(encoding='shift-jis')
    t= 15 - len(Bone.name.encode(encoding='shift-jis'))
    i= 0
    while i < t:
        vmd_wr += bytes(b'\x00')
        i += 1
    while i > t:
        vmd_wr -= bytes(b'\x00')
        t += 1

    vmd_wr += Bone.frame.to_bytes(4, 'little')
    vmd_wr += struct.pack('f', Bone.posX)
    vmd_wr += struct.pack('f', Bone.posY)
    vmd_wr += struct.pack('f', Bone.posZ)
    vmd_wr += struct.pack('f', Bone.rotX)
    vmd_wr += struct.pack('f', Bone.rotY)
    vmd_wr += struct.pack('f', Bone.rotZ)
    vmd_wr += struct.pack('f', Bone.rotW)
    vmd_wr += Bone.curve

    with open(OutputVMD, mode="ab") as outVmd:
        outVmd.write(vmd_wr)                                                                      #Write the input binary data as vmd file.
    
    return


def encodeFace(Face=Face, faceKeyCount = int):              #need to implement the "write to disk" method here
    global blocksWritten
    vmd_wr = bytes()
    
    if blocksWritten == 1:
        blocksWritten = 2
        vmd_wr = faceKeyCount.to_bytes(4, byteorder='little')

    vmd_wr += Face.name.encode(encoding='shift-jis')    
    if len(Face.name.encode(encoding='shift-jis')) <= 15:        #Need to add some blank bytes so this field is alwas 15 bytes long
        t= 15 - len(Face.name.encode(encoding='shift-jis'))
        i= 0
        while i < t:
            vmd_wr += bytes(b'\x00')
            i += 1
            #print('Added one Byte')
    else:
        #print('Removed one byte')
        while len(Face.name.encode(encoding='shift-jis')) > 15:
            Face.name = Face.name[:-1]   

    vmd_wr += Face.frame.to_bytes(4, 'little')
    vmd_wr += struct.pack('f', Face.weight)

    with open(OutputVMD, mode="ab") as outVmd:
        outVmd.write(vmd_wr)
        #print("File Write")

    return

def encodeCam(Cam=Cam, camCount = int):
    global blocksWritten
    vmd_wr = bytes()

    while blocksWritten < 2:
        vmd_wr += bytes(b'\x00\x00\x00\x00')
        blocksWritten += 1
    if blocksWritten == 2:
        blocksWritten = 3
        vmd_wr += camCount.to_bytes(4, 'little')

    vmd_wr += Cam.frame.to_bytes(4, 'little')
    vmd_wr += struct.pack('f', Cam.distance)
    vmd_wr += struct.pack('f', Cam.posX)
    vmd_wr += struct.pack('f', Cam.posY)   
    vmd_wr += struct.pack('f', Cam.posZ)
    vmd_wr += struct.pack('f', Cam.rotX)
    vmd_wr += struct.pack('f', Cam.rotY)
    vmd_wr += struct.pack('f', Cam.rotZ)       
    vmd_wr += ast.literal_eval(Cam.curve)
    vmd_wr += Cam.fov.to_bytes(4, 'little')
    vmd_wr += Cam.per.to_bytes(1, 'little')
    
    with open(OutputVMD, mode="ab") as outVmd:
        outVmd.write(vmd_wr)
    return

def readCsv():
    with open(InCsv, encoding=encoding) as Csv:
        reader = csv.reader(Csv)
        i = 0
        dataType = 0              #0=Header, 1=Bones, 2=Face, 3=Camera

        for row in reader:                      #Main loop to read the csv
            #tartTime = time.time()
            i += 1

            if row[0] == '#---Bone Data---':    #Determine data type.
                dataType = 1
                print('Working on bones...')
                next(reader)
                continue              

            if row[0] == '#---Face Data---':
                dataType = 2
                print('Working on morphs...')
                next(reader)
                continue

            if row[0] == '#Camera Data':
                next(reader)
                print('Working on camera...')
                dataType = 3
                continue


            if i == 2:
                modelName = row[0]
                boneKeyCount = int(row[1])
                faceKeyCount = int(row[2])
                camKeyCount = int(row[3])

                encodeHeader(modelName, boneKeyCount, faceKeyCount, camKeyCount)


            if dataType == 1:
                #print('weso')
                try:
                    Bone.iteration = row[0]
                    Bone.name = row[1]
                    Bone.frame = int(row[2])
                    Bone.posX = float(row[3].replace('(', '').replace(')','').replace(',',''))
                    Bone.posY = float(row[4].replace('(', '').replace(')','').replace(',',''))
                    Bone.posZ = float(row[5].replace('(', '').replace(')','').replace(',',''))
                    Bone.rotX = float(row[6].replace('(', '').replace(')','').replace(',',''))
                    Bone.rotY = float(row[7].replace('(', '').replace(')','').replace(',',''))
                    Bone.rotZ = float(row[8].replace('(', '').replace(')','').replace(',',''))
                    Bone.rotW = float(row[9].replace('(', '').replace(')','').replace(',',''))
                    Bone.curve = ast.literal_eval(row[10])

                    encodeBones(Bone)
                except Exception as err:
                    print('*** Error while reading CSV file, on line:', i)
                    exit(err)
                

            if dataType == 2:
                try:
                    #print('This is face')  #For face data block
                    Face.iteration = row[0]
                    Face.name = row[1]
                    Face.frame = int(row[2])
                    Face.weight = float(row[3].replace('(', '').replace(')','').replace(',',''))    #I know i know, ugly af, but it works.

                    #print('Face Iteration:', Face.iteration)
                    #print('Face Name:', Face.name)
                    #print('Face Frame:', Face.frame)
                    #print('Face Weight:', Face.weight)

                    encodeFace(Face, faceKeyCount)
                except Exception as err:
                    print('*** Error while reading CSV file, on line:', i)
                    exit(err)


            if dataType == 3: 
                try:         #For camera data block
                    #print('This is cam')
                    Cam.iteration = row[0]
                    Cam.frame = int(row[1])
                    Cam.distance = float(row[2].replace('(', '').replace(')','').replace(',',''))
                    Cam.posX = float(row[3].replace('(', '').replace(')','').replace(',',''))
                    Cam.posY = float(row[4].replace('(', '').replace(')','').replace(',',''))
                    Cam.posZ = float(row[5].replace('(', '').replace(')','').replace(',',''))
                    Cam.rotX = float(row[6].replace('(', '').replace(')','').replace(',',''))
                    Cam.rotY = float(row[7].replace('(', '').replace(')','').replace(',',''))
                    Cam.rotZ = float(row[8].replace('(', '').replace(')','').replace(',',''))
                    Cam.fov = int(row[9])
                    Cam.per = int(row[10])  
                    Cam.curve = row[11]

                    #print('Cam.iteration:', Cam.iteration)
                    #print('Cam.frame:', Cam.frame)
                    #print('Cam.distance:', Cam.distance)
                    #print('Cam.posX:', Cam.posX)
                    #print('Cam.posY:', Cam.posY)
                    #print('Cam.posZ:', Cam.posZ)
                    #print('Cam.rotX:', Cam.rotX)
                    #print('Cam.rotX:', Cam.rotX)
                    #print('Cam.rotX:', Cam.rotX)
                    #print('Cam.fov:', Cam.fov)
                    #print('Cam.per:', Cam.per)
                    #print('Cam.curve:', Cam.curve)

                    encodeCam(Cam, camKeyCount)
                except Exception as err:
                    print('*** Error while reading CSV file, on line:', i,)
                    exit(err)

            #endTime = time.time()
            #print('Elapsed time:', (endTime - startTime))
            #print('End of for loop')

def fixVMD():
    global blocksWritten
    vmd_wrf = bytes()
    while blocksWritten < 6:                        #Should only run when VMD --> CSV
            vmd_wrf += bytes(b'\x00\x00\x00\x00')
            blocksWritten += 1
            print('Added 4 blank bytes')
    
    with open(OutputVMD, mode="ab") as outVmd:
        outVmd.write(vmd_wrf) #Finalize vmd file, meaning 0 light blocks and 0 shadow blocks. Will change later.
        print('Finished Writing')
            

###     Decide What to do       ###
print('*** Starting ***')
#print ('Args:', len(sys.argv))

if len(sys.argv) == 3:          #If for some reason compiling this, might need to change this to 2 and ofset every sys.argv by -1
    inPath = sys.argv[1]
    outPath = sys.argv[2]

    if pathlib.Path(inPath).suffix == '.vmd':    #Set VMD --> CSV mode
        Input = inPath                           #Input is only for vmd input
        OutCsv = outPath
        #print('file is vmd')

        if pathlib.Path(OutCsv).suffix != '.csv':   #usefull if argument given is a folder (I think)
            OutCsv += ' out.csv'
        
        print()
        print('VMD --> CSV')
        vmd_bin = readVmd(Input)        #Start decoding
        magiString, modelName, boneKeyCount, faceKeyCount, camKeyCount, faceBytePos, camBytePos, excessData = decodeStart(vmd_bin)
        writeCsv(OutCsv)

    elif pathlib.Path(inPath).suffix == '.csv':  #Set CSV --> VMD mode
        InCsv = inPath
        OutputVMD = outPath
        #print('file is csv')

        if pathlib.Path(OutputVMD).suffix != '.vmd':
            OutputVMD += ' out.vmd'

        print()
        print('CSV --> VMD')
        readCsv()                       #Start encoding
        fixVMD()

    else:
        print('Unable to detect imput file type. Exiting...')
        exit()
        
elif len(sys.argv) == 2:    #When only given one arg, assume its output
    outPath = sys.argv[1]
    if pathlib.Path(outPath).suffix == '':
        print('Error. Please specify the output format.')
        exit()
    
    if pathlib.Path(outPath).suffix == '.vmd':
        inPath = tkinter.filedialog.askopenfilename(initialdir='./', title='Open CSV file', filetypes=[('Comma Separated Values', '*.csv')])
        InCsv = inPath
        OutputVMD = outPath

        print()
        print('CSV --> VMD')
        readCsv()
        fixVMD()

    elif pathlib.Path(outPath).suffix == '.csv':
        inPath = tkinter.filedialog.askopenfilename(initialdir='./', title='Open VMD file', filetypes=[('Vocaloid Motion Data', '*.vmd')])
        Input = inPath
        OutCsv = outPath

        print()
        print('VMD --> CSV')
        vmd_bin = readVmd(Input)        #Start decoding
        magiString, modelName, boneKeyCount, faceKeyCount, camKeyCount, faceBytePos, camBytePos, excessData = decodeStart(vmd_bin)
        writeCsv(OutCsv)
    
    else:
        print('Unable to determine output file type. Exiting...')
        exit()

elif len(sys.argv) < 2:
    inPath = tkinter.filedialog.askopenfilename(initialdir='./', title='Select Input file', filetypes=[('Compatible Files', '*.vmd *.csv'), ('Vocaloid Motion Data', '*.vmd'), ('Comma Separated Values', '*.csv')])

    if pathlib.Path(inPath).suffix == '.vmd':
        outPath = tkinter.filedialog.asksaveasfilename(initialdir='./', title='Save CSV file', filetype=[('Comma Separated Values', '*.csv')], defaultextension='.csv')
        Input = inPath
        OutCsv = outPath

        print()
        print('VMD --> CSV')
        vmd_bin = readVmd(Input)        #Start decoding
        magiString, modelName, boneKeyCount, faceKeyCount, camKeyCount, faceBytePos, camBytePos, excessData = decodeStart(vmd_bin)
        writeCsv(OutCsv)

    elif pathlib.Path(inPath).suffix == '.csv':
        outPath = tkinter.filedialog.asksaveasfilename(initialdir='./', title='Save VMD file', filetype=[('Vocaloid Motion Data', '*.vmd')], defaultextension='.vmd')
        InCsv = inPath
        OutputVMD = outPath
        print()
        print('CSV --> VMD')
        readCsv()
        fixVMD()

    else:
        print('Unable to determine input file type. Exiting...')
        exit()


endTime = time.time()
print()
print('Conversion completed!')   
print('Elapsed time:', (endTime - startTime), 'seconds')


### Notes on VMD binary structure ###
# 
# 50 Bytes - Header
#   30 Bytes (shift-jis) - File signature.
#   20 Bytes (shift-jis) - Model Name (Sometimes used for motion name, doesnt really matter)
#
# 4 Bytes (int) - Number of bone keyframes
#   111 bytes - Bone data
#       15 bytes - Bone name
#       4 bytes (int) - Index of the keyframe (Not all keyframes have to be continuos. This tells the animation software, MikuMikuDance, Blender, etc; where to put the frame)
#       4 bytes (float) - Cordinate X
#       4 bytes (float) - Cordinate Y
#       4 bytes (float) - Cordinate Z
#       4 bytes (float) - Rotation X
#       4 bytes (float) - Rotation Y
#       4 bytes (float) - Rotation Z
#       4 bytes (float) - Rotation W
#       64 bytes (bin) - Intrapolation data. (Binary representation of the bezier curve. Not gonna pretend like i know what this is lol)
#
# 4 Bytes (int) - Number of face/morph keyframes
#   23 Bytes - Facial data
#       15 bytes (shift-jis) - ShapeKey/Morph name
#       4 bytes (int) - Index of the Morph
#       4 bytes (float) - Weight of the morph to be applied.
#       
# 
# 4 Bytes (int) - Number of camera keyframes
#   61 bytes - Camera data
#       4 bytes (int) - Index of the keyframe
#       4 bytes (float) - Distance from camera to target
#       4 bytes (float) - Target X position
#       4 bytes (float) - Target Y position
#       4 bytes (float) - Target Z position
#       4 bytes (float) - Target X rotation
#       4 bytes (float) - Target Y rotation
#       4 bytes (float) - Target Z rotation
#       24 bytes (bin) - Camera interpolation (Also bezier curves. Format "Should" be the same as used on the bones)
#       4 bytes (int) - Camera FOV angle
#       1 byte (bool saved as int) - Perspective/Orthographic toggle (0=Perspectic, 1=Ortographic)
#
# 4 Bytes (int) - Number of lamp/Light keyframes (Yeah, apparently vmd can also store light animation)
#   28 bytes - Light data (I might implement conversion for this later, i'll need to reverse engineer this...)
#
# 4 Bytes (int) - Number of Self Shadow keyframes (needs testing, no idea what's this about)
#   9 bytes - Shadow data. (I also have no idea what this even is)
#
#
# The header is fixed lenght, aswell as the data inside of every block. The only thing that can variate the lenght of the file, is the ammount of data blocks
# All strings are encoded as shift-jis
# The header has no termination
# Strings used in names are null terminated
# All numerical values are little endian
# All ints are 4 byte unsigned
# All floats are Single float32
#
# Rotation of the bones is saved as a Quaternion, hence the 'W' parameter
# Rotation of the camera is saved as Euler.
# Translation and rotation of the camera is applied to the target (parent of the camera)
# Distance is applied to the camera object.
