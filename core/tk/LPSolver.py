from typing import List
from cvxopt import matrix, solvers
#use glpk, bomb out early - nothing we're doing is that complicated
solvers.options['glpk'] = {'tm_lim': 1000}
import numpy as np
np.random.seed(0)


class LPSolver():
	"""
	Encapsulates a basic Linear Programming solver for multi-agent Zero Sum Game
	"""
	def __init__(self, verbose=False, solver="glpk"):
		self.solver = solver
		if not verbose:
			solvers.options['show_progress'] = False
			solvers.options['glpk'] = {'msg_lev': 'GLP_MSG_OFF'}

	# @tf(True)
	def max_min(self, payout_player1):
		'''
		Formulate the game in the standard player1 format,
		and send in the row major payoff as a list of List.
		Returns Qs for each action.
		'''
		actions = len(payout_player1)
		#create the minimize matrix c
		c = [-1] + [0 for _ in range(actions)]
		c = np.array(c, dtype="float")
		c = matrix(c)
		#?do we need to flip the sign on c?

		#create constraints for G*x <= h based on payout matrix
		#the input is row major, transpose this
		G = np.matrix(payout_player1, dtype="float").T
		#Automatically add the x > 0 constraint for each action
		#safe because we are expecting probabilities out of this
		G = np.vstack([G, np.eye(actions)])
		# cvxopt works with minimization constraint,
		# so flip the sign on all elements
		G *= -1
		# insert utility column
		new_col = [1 for _ in range(actions)] + [0 for _ in range(actions)]
		G = np.insert(G, 0, new_col, axis=1)
		G = matrix(G)

		h = ([0 for i in range(actions)] +
				[0 for _ in range(actions)])
		h = np.array(h, dtype="float")
		h = matrix(h)

		# contraints Ax = b
		A = [0] + [1 for _ in range(actions)]
		A = np.matrix(A, dtype="float")
		A = matrix(A)

		b = np.matrix(1, dtype="float")
		b = matrix(b)

		res = solvers.lp(c=c, G=G, h=h, A=A, b=b, solver=self.solver)
		a = np.array(res['x'])
		#ignore the utilitycolumn, and a is a 2D array
		ret = [ a[i][0] for i in range(1,len(a))]
		return ret



if __name__ == "__main__":
	sw = 150
	sh= 100

	# portrait mode
	iw = 15
	ih = 10

	if sh >= sw:
		if ih >= iw:
			A =matrix( [
				[1.0,0.0,-1.0,0.0,ih/iw] #ih/iw comes here for portrait
				,[0.0,1.0,0.0,-1.0, -1] #iw/ih comes here for landscape
			])
		else:
			A =matrix( [
				[1.0,0.0,-1.0,0.0,-1] #ih/iw comes here for portrait
				,[0.0,1.0,0.0,-1.0, iw/ih] #iw/ih comes here for landscape
			])
	else:
		if ih >= iw:
			A =matrix( [
				[1.0,0.0,-1.0,0.0,-1] #ih/iw comes here for portrait
				,[0.0,1.0,0.0,-1.0, iw/ih] #iw/ih comes here for landscape
			])
		else:
			A =matrix( [
				[1.0,0.0,-1.0,0.0,ih/iw] #ih/iw comes here for portrait
				,[0.0,1.0,0.0,-1.0, -1] #iw/ih comes here for landscape
			])

	b=matrix([float(sw),float(sh),0.0,0.0,0.0])
	c = matrix([-1.0,-1.0])
	sol=solvers.lp(c,A,b)
	print(sol['x'])
	x = int(sol['x'][0])
	y = int(sol['x'][1])
	print(x,y)
	# sol = LPSolver()
	# print(sol.solve(A,b,c))

	# A = matrix([ [-1.0, -1.0, 0.0, 1.0], [1.0, -1.0, -1.0, -2.0] ])
	# b = matrix([ 1.0, -2.0, 0.0, 4.0 ])
	# c = matrix([ 2.0, 1.0 ])
	# sol=solvers.lp(c,A,b)
	# print(sol['x'])
