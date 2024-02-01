# Optimal Liquidity Pool Graphs

As a product of my master thesis I have three python scripts to present

## convexCalculateTrade.py
This code is an implementation of [Angeris CFMM router](https://angeris.github.io/papers/cfmm-routing.pdf). It reads in the information for the current liquidity pool graph from the config.json file, formulates the convex optimization problem, calls the cvxpy library which solves it with the SCS solver.

## convexOptimizeTrade.py
This code is an extension of the code in convexCalculateTrade.py. The initial configuration is now part of the optimization problem. It also needs the config.json file to run.

## packageRouter.py
This code is calculates a new lower bound on exchanges in CPMM liquidity pool graphs and then does a gradient descent to find a configuration with the best lower bound. This code also needs the config.json file to run.

