import os

def GetFreeMem():
    # Get the status of the file system
    stat = os.statvfs('/')

    # Calculate the available space
    block_size = stat[0]  # Size of a block
    total_blocks = stat[2]  # Total data blocks in the file system
    free_blocks = stat[3]  # Free blocks in the file system

    # Calculate total and free space in bytes
    total_space = block_size * total_blocks
    free_space = block_size * free_blocks

    return free_space

print(GetFreeMem())