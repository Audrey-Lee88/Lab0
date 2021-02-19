'''Code file for badminton elimination lab created for Advanced Algorithms
Spring 2021 at Olin College. The code for this lab has been adapted from:
https://github.com/ananya77041/baseball-elimination/blob/master/src/BaseballElimination.java'''

import sys
import math
import picos as pic
import networkx as nx
import itertools
import cvxopt
import numpy as np
import matplotlib.pyplot as plt


class Division:
    '''
    The Division class represents a badminton division. This includes all the
    teams that are a part of that division, their winning and losing history,
    and their remaining games for the season.

    filename: name of a file with an input matrix that has info on teams &
    their games
    '''

    def __init__(self, filename):
        self.teams = {}
        self.G = nx.DiGraph()
        self.readDivision(filename)

    def readDivision(self, filename):
        '''Reads the information from the given file and builds up a dictionary
        of the teams that are a part of this division.

        filename: name of text file representing tournament outcomes so far
        & remaining games for each team
        '''
        f = open(filename, "r")
        lines = [line.split() for line in f.readlines()]
        f.close()

        lines = lines[1:]
        for ID, teaminfo in enumerate(lines):
            team = Team(int(ID), teaminfo[0], int(teaminfo[1]), int(teaminfo[2]), int(teaminfo[3]), list(map(int, teaminfo[4:])))
            self.teams[ID] = team

    def get_team_IDs(self):
        '''Gets the list of IDs that are associated with each of the teams
        in this division.

        return: list of IDs that are associated with each of the teams in the
        division
        '''
        return self.teams.keys()

    def is_eliminated(self, teamID, solver):
        '''Uses the given solver (either Linear Programming or Network Flows)
        to determine if the team with the given ID is mathematically
        eliminated from winning the division (aka winning more games than any
        other team) this season.

        teamID: ID of team that we want to check if it is eliminated
        solver: string representing whether to use the network flows or linear
        programming solver
        return: True if eliminated, False otherwise
        '''
        flag1 = False
        team = self.teams[teamID]

        temp = dict(self.teams)
        del temp[teamID]

        for _, other_team in temp.items():
            if team.wins + team.remaining < other_team.wins:
                flag1 = True

        saturated_edges = self.create_network(teamID)
        if not flag1:
            if solver == "Network Flows":
                flag1 = self.network_flows(saturated_edges)
            elif solver == "Linear Programming":
                flag1 = self.linear_programming(saturated_edges)

        return flag1
    

    def create_network(self, teamID):
        '''Builds up the network needed for solving the badminton elimination
        problem as a network flows problem & stores it in self.G. Returns a
        dictionary of saturated edges that maps team pairs to the amount of
        additional games they have against each other.
        teamID: ID of team that we want to check if it is eliminated
        return: dictionary of saturated edges that maps team pairs to
        the amount of additional games they have against each other
        '''
        #sets up saturated_edges dictionary
        saturated_edges = {}
        base_cap = self.teams[teamID].wins + self.teams[teamID].remaining 
        for team in self.teams.values():
            if team != teamID:
                for oteam in self.teams.values():
                    if team != oteam and oteam != teamID:
                        if (oteam.name,team.name) not in saturated_edges:
                            saturated_edges[(team.name,oteam.name)] = team.get_against(oteam.ID)
                            #adds edges to sink
                            self.G.add_edge(team.name,"sink",capacity = base_cap-team.wins)
                            self.G.add_edge(oteam.name,"sink",capacity = base_cap-oteam.wins)

        #adds saturated edges to self.G from source
        for pair in saturated_edges.keys():
            self.G.add_edge("source",pair,capacity=saturated_edges[pair]) 
            self.G.add_edge("source",pair,capacity=saturated_edges[pair])

        #adds intermediatary edges
        for (name1,name2) in saturated_edges.keys():
            self.G.add_edge((name1,name2),name2,capacity = np.Inf)
            self.G.add_edge((name1,name2),name1,capacity = np.Inf)

        #keep track of flow/add in flow -- nx maximum_flow function now worked, so we don't need this anymore and can delete out flow attribute from the edges above.
        #for (name1,name2) in saturated_edges.keys():
         #   if self.G["source"][(name1,name2)]["flow"] < self.G["source"][(name1,name2)]["capacity"]:
          #      if  self.G["source"][(name1,name2)]["capacity"] <= (self.G[name2]["sink"]["capacity"] - self.G[name2]["sink"]["flow"]):
           #         self.G["source"][(name1,name2)]["flow"] = self.G["source"][(name1,name2)]["capacity"]
            #        self.G[name2]["sink"]["flow"] = self.G[name2]["sink"]["flow"] + self.G["source"][(name1,name2)]["flow"]
             #   if self.G["source"][(name1,name2)]["capacity"] <= (self.G[name1]["sink"]["capacity"] - self.G[name1]["sink"]["flow"]):
              #      self.G["source"][(name1,name2)]["flow"] = self.G["source"][(name1,name2)]["capacity"]
               #     self.G[name1]["sink"]["flow"] = self.G[name1]["sink"]["flow"] + self.G["source"][(name1,name2)]["flow"]
                #elif self.G["source"][(name1,name2)]["capacity"] > (self.G[name2]["sink"]["capacity"] - self.G[name2]["sink"]["flow"]):
                 #   self.G["source"][(name1,name2)]["flow"] = self.G[name2]["sink"]["capacity"]
                  #  self.G[name2]["sink"]["flow"] = self.G[name2]["sink"]["capacity"]
               # elif self.G["source"][(name1,name2)]["capacity"] > (self.G[name1]["sink"]["capacity"] - self.G[name1]["sink"]["flow"]):
                #    self.G["source"][(name1,name2)]["flow"] = self.G[name1]["sink"]["capacity"]
                 #   self.G[name1]["sink"]["flow"] = self.G[name1]["sink"]["capacity"]
           
        return saturated_edges


    def network_flows(self, saturated_edges):
        '''Uses network flows to determine if the team with given team ID
        has been eliminated. You can feel free to use the built in networkx
        maximum flow function or the maximum flow function you implemented as
        part of the in class implementation activity.

        saturated_edges: dictionary of saturated edges that maps team pairs to
        the amount of additional games they have against each other
        return: True if team is eliminated, False otherwise
        '''
        flow_val,flow_dist = nx.maximum_flow(self.G,"source","sink")
        for pair in saturated_edges.keys():
            if self.G["source"][pair]["capacity"] - flow_dist["source"][pair] > 0:
            #This line not relevant: Used only if you calaculate flows by hand...if self.G["source"][pair]["capacity"] - self.G["source"][pair]["flow"] > 0:
                return True
        return False

    def linear_programming(self, saturated_edges):
        '''Uses linear programming to determine if the team with given team ID
        has been eliminated. We recommend using a picos solver to solve the
        linear programming problem once you have it set up.
        Do not use the flow_constraint method that Picos provides (it does all of the work for you)
        We want you to set up the constraint equations using picos (hint: add_constraint is the method you want)

        saturated_edges: dictionary of saturated edges that maps team pairs to
        the amount of additional games they have against each other
        returns True if team is eliminated, False otherwise
        '''

        maxflow=pic.Problem()

        #TODO: implement this
        # we recommend using the 'cvxopt' solver once you set up the problem

        return False


    def checkTeam(self, team):
        '''Checks that the team actually exists in this division.
        '''
        if team.ID not in self.get_team_IDs():
            raise ValueError("Team does not exist in given input.")

    def __str__(self):
        '''Returns pretty string representation of a division object.
        '''
        temp = ''
        for key in self.teams:
            temp = temp + f'{key}: {str(self.teams[key])} \n'
        return temp

class Team:
    '''
    The Team class represents one team within a badminton division for use in
    solving the badminton elimination problem. This class includes information
    on how many games the team has won and lost so far this season as well as
    information on what games they have left for the season.

    ID: ID to keep track of the given team
    teamname: human readable name associated with the team
    wins: number of games they have won so far
    losses: number of games they have lost so far
    remaining: number of games they have left this season
    against: dictionary that can tell us how many games they have left against
    each of the other teams
    '''

    def __init__(self, ID, teamname, wins, losses, remaining, against):
        self.ID = ID
        self.name = teamname
        self.wins = wins
        self.losses = losses
        self.remaining = remaining
        self.against = against

    def get_against(self, other_team=None):
        '''Returns number of games this team has against this other team.
        Raises an error if these teams don't play each other.
        '''
        try:
            num_games = self.against[other_team]
        except:
            raise ValueError("Team does not exist in given input.")

        return num_games

    def __str__(self):
        '''Returns pretty string representation of a team object.
        '''
        return f'{self.name} \t {self.wins} wins \t {self.losses} losses \t {self.remaining} remaining'

if __name__ == '__main__':
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        division = Division(filename)
        for (ID, team) in division.teams.items():
            print(f'{team.name}: Eliminated? {division.is_eliminated(team.ID, "Network Flows")}')
    else:
        print("To run this code, please specify an input file name. Example: python badminton_elimination.py teams2.txt.")
