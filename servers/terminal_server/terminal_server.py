#!/usr/bin/env python3

import os
import asyncio
import aiofiles
import aiofiles.os
import fnmatch
import json
from datetime import datetime
from typing import List, Dict, Union
from mcp.server.fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP("secure-filesystem-server")

# ✅ Directly define allowed directories here
allowed_directories: List[str] = [os.path.expanduser("~/mcp/workspace")]

def normalize_path(p: str) -> str:
    return os.path.normpath(os.path.abspath(os.path.expanduser(p)))

def is_within_allowed(path: str) -> bool:
    return any(os.path.commonpath([path, ad]) == ad for ad in allowed_directories)

async def validate_path(requested_path: str) -> str:
    path = normalize_path(requested_path)
    if not is_within_allowed(path):
        raise PermissionError(f"Access denied: {path} is outside allowed directories.")
    return path

@mcp.tool()
async def list_allowed_directories() -> List[str]:
    return allowed_directories

@mcp.tool()
async def read_file(path: str) -> str:
    valid_path = await validate_path(path)
    async with aiofiles.open(valid_path, mode='r', encoding='utf-8') as f:
        return await f.read()

@mcp.tool()
async def write_file(path: str, content: str) -> str:
    valid_path = await validate_path(path)
    async with aiofiles.open(valid_path, mode='w', encoding='utf-8') as f:
        await f.write(content)
    return f"Successfully wrote to {path}"

@mcp.tool()
async def edit_file(path: str, edits: List[Dict[str, str]], dry_run: bool = False) -> str:
    valid_path = await validate_path(path)
    async with aiofiles.open(valid_path, mode='r', encoding='utf-8') as f:
        content = await f.read()

    original_lines = content.splitlines()
    modified_lines = original_lines.copy()

    for edit in edits:
        old = edit['oldText']
        new = edit['newText']
        try:
            index = modified_lines.index(old)
            modified_lines[index] = new
        except ValueError:
            raise ValueError(f"Text to replace not found: {old}")

    diff = '\n'.join(modified_lines)
    if not dry_run:
        async with aiofiles.open(valid_path, mode='w', encoding='utf-8') as f:
            await f.write('\n'.join(modified_lines))
    return diff

@mcp.tool()
async def create_directory(path: str) -> str:
    valid_path = await validate_path(path)
    await aiofiles.os.makedirs(valid_path, exist_ok=True)
    return f"Successfully created directory {path}"

@mcp.tool()
async def list_directory(path: str) -> List[str]:
    valid_path = await validate_path(path)
    entries = await aiofiles.os.listdir(valid_path)
    result = []
    for entry in entries:
        full_path = os.path.join(valid_path, entry)
        if await aiofiles.os.path.isdir(full_path):
            result.append(f"[DIR] {entry}")
        else:
            result.append(f"[FILE] {entry}")
    return result

@mcp.tool()
async def directory_tree(path: str) -> Dict[str, Union[str, List]]:
    valid_path = await validate_path(path)

    async def build_tree(current_path: str) -> Dict[str, Union[str, List]]:
        tree = {"name": os.path.basename(current_path), "type": "directory", "children": []}
        entries = await aiofiles.os.listdir(current_path)
        for entry in entries:
            full_path = os.path.join(current_path, entry)
            if await aiofiles.os.path.isdir(full_path):
                subtree = await build_tree(full_path)
                tree["children"].append(subtree)
            else:
                tree["children"].append({"name": entry, "type": "file"})
        return tree

    return await build_tree(valid_path)

@mcp.tool()
async def move_file(source: str, destination: str) -> str:
    valid_source = await validate_path(source)
    valid_destination = await validate_path(destination)
    await aiofiles.os.rename(valid_source, valid_destination)
    return f"Successfully moved {source} to {destination}"

@mcp.tool()
async def search_files(path: str, pattern: str, exclude_patterns: List[str] = []) -> List[str]:
    valid_path = await validate_path(path)
    matches = []

    for root, dirs, files in os.walk(valid_path):
        rel_root = os.path.relpath(root, valid_path)
        if any(fnmatch.fnmatch(rel_root, pat) for pat in exclude_patterns):
            continue
        for name in files:
            if fnmatch.fnmatch(name, pattern):
                matches.append(os.path.join(root, name))
    return matches

@mcp.tool()
async def get_file_info(path: str) -> Dict[str, Union[str, int]]:
    valid_path = await validate_path(path)
    stat = await aiofiles.os.stat(valid_path)
    return {
        "size": stat.st_size,
        "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "accessed": datetime.fromtimestamp(stat.st_atime).isoformat(),
        "is_directory": await aiofiles.os.path.isdir(valid_path),
        "is_file": await aiofiles.os.path.isfile(valid_path),
        "permissions": oct(stat.st_mode)[-3:]
    }

if __name__ == "__main__":
    mcp.run()
