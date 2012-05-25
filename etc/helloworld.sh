#!/bin/sh
#SBATCH --job-name=helloworld
#SBATCH --output=helloworld_%j.out
#SBATCH --error=helloworld_%j.err
#SBATCH --time=1

srun helloworld
