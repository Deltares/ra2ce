#!/usr/bin/env bash
pixi install
git config --global core.autocrlf true
git config --global --add safe.directory "/usr/src/app"