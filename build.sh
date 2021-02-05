#!/bin/sh

cd agent/ && sh build.sh && cd ..
cd server/ && sh build.sh && cd ..
