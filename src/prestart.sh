#!/usr/bin/env bash
echo "## Run alembic migrations ##"
alembic upgrade head
echo "### Success updated ###"
