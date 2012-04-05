#!/bin/sh
#SBATCH --job-name=helloworld
#SBATCH --output=helloworld_%j.out
#SBATCH --error=helloworld_%j.err
#SBATCH --nodes 4
#SBATCH --time=1

srun helloworld
