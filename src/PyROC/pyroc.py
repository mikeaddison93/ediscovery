#!/usr/bin/env python
# encoding: utf-8
"""
PyRoc.py

Created by Marcel Caraciolo on 2009-11-16.
Copyright (c) 2009 Federal University of Pernambuco. All rights reserved.

IMPORTANT:
Based on the original code by Eithon Cadag (http://www.eithoncadag.com/files/pyroc.txt)

Python Module for calculating the area under the receive operating characteristic curve, given a dataset.

0.1  - First Release
0.2 - Updated the code by adding new metrics for analysis with the confusion matrix.

"""

import random
import math
try:
	import pylab
except:
	print "error:\tcan't import pylab module, you must install the module:\n"
	print "\tmatplotlib to plot charts!'\n"


def random_mixture_model(pos_mu=.6,pos_sigma=.1,neg_mu=.4,neg_sigma=.1,size=200):
	pos = [(1,random.gauss(pos_mu,pos_sigma),) for _ in xrange(size/2)]
	neg = [(0,random.gauss(neg_mu,neg_sigma),) for _ in xrange(size/2)]
	return pos+neg


def plot_multiple_rocs_separate(rocList,title='', labels = None, equal_aspect = True):
	""" Plot multiples ROC curves as separate at the same painting area. """
	pylab.clf()
	pylab.title(title)
	for ix, r in enumerate(rocList):
		ax = pylab.subplot(4,4,ix+1)
		pylab.ylim((0,1))
		pylab.xlim((0,1))
		ax.set_yticklabels([])
		ax.set_xticklabels([])
		if equal_aspect:
			cax = pylab.gca()
			cax.set_aspect('equal')
		
		if not labels:
			labels = ['' for x in rocList]
		
		pylab.text(0.2,0.1,labels[ix],fontsize=8)
		pylab.plot([x[0] for x in r.derived_points],[y[1] for y in r.derived_points], 'r-',linewidth=2)
	
	pylab.show()
	


def _remove_duplicate_styles(rocList):
	""" Checks for duplicate line styles and replaces duplicates with a random one."""
	pref_styles = ['cx-','mx-','yx-','gx-','bx-','rx-']
	points = 'ov^>+xd'
	colors = 'bgrcmy'
	lines = ['-','-.',':']
	
	rand_ls = []
	
	for r in rocList:
		if r.linestyle not in rand_ls:
			rand_ls.append(r.linestyle)
		else:
			while True:
				if len(pref_styles) > 0:
					pstyle = pref_styles.pop()
					if pstyle not in rand_ls:
						r.linestyle = pstyle
						rand_ls.append(pstyle)
						break
				else:
					ls = ''.join(random.sample(colors,1) + random.sample(points,1)+ random.sample(lines,1))
					if ls not in rand_ls:
						r.linestyle = ls
						rand_ls.append(ls)
						break
						

def plot_multiple_roc(rocList, 
					title='', 
					labels=None, 
					include_baseline=True, 
					equal_aspect=True, 
					lengend_inside=True,
					file_name=None):
	""" Plots multiple ROC curves on the same chart. 
		Parameters:
			rocList: the list of ROCData objects
			title: The tile of the chart
			labels: The labels of each ROC curve
			include_baseline: if it's  True include the random baseline
			equal_aspect: keep equal aspect for all roc curves
	"""
	from matplotlib.font_manager import FontProperties
	font0 = FontProperties()
	cust_font = font0.copy()
	cust_font.set_family('arial')
	cust_font.set_size(12)
	
	pylab.clf()
	pylab.ylim((0,1))
	pylab.xlim((0,1))
	pylab.xticks(pylab.arange(0,1.1,.1))
	pylab.yticks(pylab.arange(0,1.1,.1))
	pylab.grid(True)
	if equal_aspect:
		cax = pylab.gca()
		cax.set_aspect('equal')
	pylab.tick_params(axis='both', which='major', labelsize=10)
	pylab.tick_params(axis='both', which='minor', labelsize=10)
			
	pylab.xlabel('False Positive Rate', fontproperties=cust_font) # 1 - True Negative Rate
	pylab.ylabel('True Positive Rate (Recall)', fontproperties=cust_font) # Sensitivity 

	pylab.title(title)
	
	if not labels: labels = [ '' for x in rocList]
	
	_remove_duplicate_styles(rocList)
	
	for ix, r in enumerate(rocList):
		pylab.plot([x[0] for x in r.derived_points], 
				[y[1] for y in r.derived_points], 
				r.linestyle, 
				linewidth=1, 
				label=labels[ix] + ', AUC: %.2f' % r.auc())
	
	if include_baseline:
		pylab.plot([0.0,1.0], [0.0, 1.0], 'k-', label= 'Random Guess')
	
#		pylab.annotate('Line of Perfect Classification', xy=(0, 1), xytext=(.1, .9),
#	            arrowprops=dict(facecolor='black', shrink=0.05))
#		pylab.annotate('Line of No-discrimination', xy=(0.55, 0.55), xytext=(.58, .5),
#	            arrowprops=dict(facecolor='black', shrink=0.05))
	
	if labels:
		if lengend_inside: # to place inside the plot 
			pylab.legend(loc='lower right', 
						prop={'size':12, 'family':'arial'})  
		else: # to place right outside 
			pylab.legend(bbox_to_anchor=(1.02, 1), loc=2, 
						borderaxespad=0., 
						prop={'size':9, 'family':'arial'}) 
		
	if file_name:
		pylab.savefig(file_name, dpi=700, bbox_inches='tight', pad_inches=0.1)
	else:
		pylab.show() 
		
		
		

def load_decision_function(path):
	""" Function to load the decision function (DataSet) 
		Parameters:
			path: The dataset file path
		Return:
			model_data: The data modeled
	"""
	fileHandler = open(path,'r')
	reader = fileHandler.readlines()
	reader = [line.strip().split() for line in reader]
	model_data = []
	for line in reader:
		if len(line) == 0: continue
		fClass,fValue = line
		model_data.append((int(fClass), float(fValue)))
	fileHandler.close()

	return model_data
	

class ROCData(object):
	""" Class that generates an ROC Curve for the data.
		Data is in the following format: a list l of tutples t
		where:
			t[0] = 1 for positive class and t[0] = 0 for negative class
			t[1] = score
			t[2] = label
	"""
	def __init__(self,data,linestyle='rx-'):
		""" Constructor takes the data and the line style for plotting the ROC Curve.
			Parameters:
				data: The data a list of tuples t (l = [t_0,t_1,...t_n]) where:
					  t[0] = 1 for positive class and 0 for negative class
					  t[1] = a score
			 		  t[2] = any label (optional)
				lineStyle: The matplotlib style string for plots.
				
			Note: The ROCData is still usable w/o matplotlib. The AUC is still available, 
			      but plots cannot be generated.
		"""
		# Sort the tuples in the descending order of the decision scores 
		self.data = sorted(data, lambda x,y: cmp(y[1],x[1]))
		
		self.linestyle = linestyle
		
		# Seed initial points with default full ROC
		self.auc() 
	
	def auc(self, fpnum=0):
		""" 
		Uses the trapezoidal rule to calculate the area under the 
		curve. If fpnum is supplied, it will calculate a partial 
		AUC, up to the number of false positives in fpnum (the 
		partial AUC is scaled to between 0 and 1). It assumes that 
		the positive class is expected to have the higher of the 
		scores (s(+) < s(-))
		
		Parameters:
			fpnum: The cumulative FP count (fps)
		
		Return:
			The Area Under the ROC Curve (AUC) value 
		"""
		
		fps_count = 0
		relevant_pauc = []
		current_index = 0
		max_n = len([x for x in self.data if x[0] == 0]) 		
		if fpnum == 0:
			relevant_pauc = [x for x in self.data]
		elif fpnum > max_n:
			fpnum = max_n
		else:
			# Find the upper limit of the data 
			# that does not exceed n FPs
			while fps_count < fpnum:
				relevant_pauc.append(self.data[current_index])
				if self.data[current_index][0] == 0:
					fps_count += 1
				current_index += 1

		total_n = len([x for x in relevant_pauc if x[0] == 0]) # Total Negatives, (TP + FN)
		total_p = len(relevant_pauc) - total_n # Total Positives, (TN + FP)
		
		# Generate the ROC points 
		
		previous_df = -1000000.0
		current_index = 0
		points = [] # The AUC plot points 
		tp_count, fp_count = 0.0, 0.0 # TP, FP
		tpr, fpr = 0, 0 # True Positive Rate, False Positive Rate 
		
		while current_index < len(relevant_pauc):
			df = relevant_pauc[current_index][1]
			if previous_df != df:
				points.append((fpr, tpr, fp_count))
			
			if relevant_pauc[current_index][0] == 0:
				fp_count += 1
			elif relevant_pauc[current_index][0] == 1:
				tp_count += 1
			fpr = fp_count / total_n # FPR 
			tpr = tp_count / total_p # TPR 
			
			previous_df = df
			current_index += 1
		
		points.append((fpr, tpr, fp_count)) # to add the last point
		points.sort(key=lambda i: (i[0], i[1])) # sorts based on FPR and then TPR  
		self.derived_points = points
		
		return self._trapezoidal_rule(points)


	def _trapezoidal_rule(self, curve_pts):
		""" 
		Method to calculate the area under the ROC curve
		"""
#		print 
#		print 'Trapezoidal Rule to Compute AUC:'
		cum_area = 0.0
		for ix,x in enumerate(curve_pts[0:-1]):
			cur_pt = x
			next_pt = curve_pts[ix + 1]
			cum_area += 0.5 * (cur_pt[1] + next_pt[1]) * (next_pt[0] - cur_pt[0]) # 1/2 * TPR * FPR 
#			print "Line #%d: x(%.2f -> %.2f) y(%.2f -> %.2f) area(%.4f)" % (ix + 1, 
#																			cur_pt[0], next_pt[0], 
#																			cur_pt[1], next_pt[1], 
#																			0.5 * (cur_pt[1] + next_pt[1]) * (next_pt[0] - cur_pt[0]))
		return cum_area
		
	def calculateStandardError(self,fpnum=0):
		""" Returns the standard error associated with the curve.
			Parameters:
				fpnum: The cumulativr FP count (fps)
			Return:
				the standard error.
		"""
		area = self.auc(fpnum)
		
		#real positive cases
		Na =  len([ x for x in self.data if x[0] == 1])
		
		#real negative cases
		Nn =  len([ x for x in self.data if x[0] == 0])
		
		
		Q1 = area / (2.0 - area)
		Q2 = 2 * area * area / (1.0 + area)
		
		return math.sqrt( ( area * (1.0 - area)  +   (Na - 1.0) * (Q1 - area*area) +
						(Nn - 1.0) * (Q2 - area * area)) / (Na * Nn))
							
	
	def plot(self, title='', include_baseline=False, equal_aspect=True, file_name=''):
		""" Method that generates a plot of the ROC curve 
			Parameters:
				title: Title of the chart
				include_baseline: Add the baseline plot line if it's True
				equal_aspect: Aspects to be equal for all plot
		"""
		
		pylab.clf()
		pylab.plot([x[0] for x in self.derived_points], [y[1] for y in self.derived_points], self.linestyle)
		if include_baseline:
			pylab.plot([0.0,1.0], [0.0,1.0],'k-.')
		pylab.ylim((0,1))
		pylab.xlim((0,1))
		pylab.xticks(pylab.arange(0,1.1,.1))
		pylab.yticks(pylab.arange(0,1.1,.1))
		pylab.grid(True)
		if equal_aspect:
			cax = pylab.gca()
			cax.set_aspect('equal')
		pylab.xlabel('1 - Specificity (True Negative Rate)')
		pylab.ylabel('Sensitivity (Recall)')
		pylab.title(title)
		
		if file_name == '':
			pylab.show()
		else: 
			pylab.savefig(file_name, bbox_inches=0)
		
	
	def confusion_matrix(self,threshold,do_print=False):
		""" Returns the confusion matrix (in dictionary form) for a fiven threshold
			where all elements > threshold are considered 1 , all else 0.
			Parameters:
				threshold: threshold to check the decision function
				do_print:  if it's True show the confusion matrix in the screen
			Return:
				the dictionary with the TP, FP, FN, TN
		"""
		pos_points = [x for x in self.data if x[1] >= threshold]
		neg_points = [x for x in self.data if x[1] < threshold]
		tp,fp,fn,tn = self._calculate_counts(pos_points,neg_points)
		
		
		if do_print:
			print "\nConfusion Matrix: "
			print "\t Actual class"
			print "\t+(1)\t-(0)"
			print "+(1)\t%i\t%i\tPredicted" % (tp,fp)
			print "-(0)\t%i\t%i\tclass" % (fn,tn)
			print 
		
		return {'TP': tp, 'FP': fp, 'FN': fn, 'TN': tn}
		

	
	def evaluateMetrics(self,matrix,metric=None,do_print=False):
		""" Returns the metrics evaluated from the confusion matrix.
			Parameters:
				matrix: the confusion matrix
				metric: the specific metric of the default value is None (all metrics).
				do_print:  if it's True show the metrics in the screen
			Return:
				the dictionary with the Accuracy, Sensitivity (Recall), Specificity (True Negative Rate),Efficiency,
				                        PositivePredictiveValue (Precision), NegativePredictiveValue, PhiCoefficient
		"""
		
		accuracy = (matrix['TP'] + matrix['TN'])/ float(sum(matrix.values()))
		
		try: 
			sensitivity = (matrix['TP'])/ float(matrix['TP'] + matrix['FN'])
		except: 
			sensitivity = 0.0 
			
		try: 
			specificity = matrix['TN'] / float(matrix['TN'] + matrix['FP'])
		except: 
			specificity = 0.0 
			
		efficiency = (sensitivity + specificity) / 2.0
		
		try:
			positivePredictiveValue =  matrix['TP'] / float(matrix['TP'] + matrix['FP'])
		except:
			positivePredictiveValue = 0.0 

		try:
			NegativePredictiveValue = matrix['TN'] / float(matrix['TN'] + matrix['FN'])
		except:
			NegativePredictiveValue = 0.0 
		
		
		try:
			PhiCoefficient = (matrix['TP'] * matrix['TN'] - matrix['FP'] * matrix['FN'])/(
							math.sqrt( (matrix['TP'] + matrix['FP']) *
							           (matrix['TP'] + matrix['FN']) *
									   (matrix['TN'] + matrix['FP']) *
									   (matrix['TN'] + matrix['FN']))) or 1.0
		except:
			PhiCoefficient = 0.0 
		
		try:
			f1_score = 2.0 * ((positivePredictiveValue * sensitivity) / (positivePredictiveValue + sensitivity))
		except: 
			f1_score = 0.0 					
		
		if do_print:
			print '\nEvaluation metrics:'
			print 'Sensitivity (Recall):    ' , sensitivity
			print 'Specificity:             ' , specificity
			# print 'Efficiency:              ' , efficiency
			print 'Accuracy:                ' , accuracy
			print 'Precision:               ' , positivePredictiveValue
			print 'NegativePredictiveValue: ' , NegativePredictiveValue
			# print 'PhiCoefficient:          ' , PhiCoefficient
			print 'F1-score:                ' , f1_score
			print 
		
		return {'SENS': sensitivity, 'SPEC': specificity, 'ACC': accuracy, 'EFF': efficiency,
				'PPV':positivePredictiveValue, 'NPV':NegativePredictiveValue , 'PHI':  PhiCoefficient, 
				'F1':f1_score }


	def _calculate_counts(self,pos_data,neg_data):
		""" Calculates the number of false positives, true positives, false negatives and true negatives """
		tp_count = len([x for x in pos_data if x[0] == 1])
		fp_count = len([x for x in pos_data if x[0] == 0])
		fn_count = len([x for x in neg_data if x[0] == 1])
		tn_count = len([x for x in neg_data if x[0] == 0])
		return tp_count,fp_count,fn_count, tn_count
		
def demo():
	'''
	Demonstrate ROC curve analysis 
	'''
	
	ds1 = [(1, .98), (1, .89), (0, .81), (1, .79), (1, .7), (1, .69), (0, .5), (0, .49), (1, .45), (0, .2)]
	ds2 = [(0, .9), (1, .89), (0, .75), (1, .72), (0, .7), (1, .65), (1, .5), (0, .49), (0, .45), (0, .2)]
	roc_ds_list= [ROCData(ds1), ROCData(ds2)]
	rocs_img_title = 'ROC Curve Analysis (demo)'
	roc_labels = ['Classifier I', 'Classifier II']
	rocs_output_file = 'ROC-Demo.eps'
	
	plot_multiple_roc(roc_ds_list, title=rocs_img_title, 
					  labels=roc_labels, 
					  file_name=rocs_output_file)
		
if __name__ == '__main__':
	print "PyRoC - ROC Curve Generator"
	print "By Marcel Pinheiro Caraciolo (@marcelcaraciolo)"
	print "http://aimotion.blogspot.com\n"
	from optparse import OptionParser
	
	parser = OptionParser()
	parser.add_option('-f', '--file', dest='origFile', help="Path to a file with the class and decision function. The first column of each row is the class, and the second the decision score.")
	parser.add_option("-n", "--max fp", dest = "fp_n", default=0, help= "Maximum false positives to calculate up to (for partial AUC).")
	parser.add_option("-p","--plot", action="store_true", dest='plotFlag', default=False, help="Plot the ROC curve (matplotlib required)")
	parser.add_option("-t",'--title', dest= 'ptitle' , default='' , help = 'Title of plot.')
	parser.add_option("-d","--demo", action="store_true", dest='plot_demo', default=False, help="Plot the ROC curve demo (matplotlib required)")
	(options,args) = parser.parse_args()

	if options.plot_demo:
		demo()
		exit()

	if (not options.origFile):
		parser.print_help()
		exit()

	df_data = load_decision_function(options.origFile)
	roc = ROCData(df_data)
	roc_n = int(options.fp_n)
	print "ROC AUC: %s" % (str(roc.auc(roc_n)),)
	print 'Standard Error:  %s' % (str(roc.calculateStandardError(roc_n)),) 
	
	print ''
	for pt in roc.derived_points:
		print pt[0],pt[1]
		
	if options.plotFlag:
		roc.plot(options.ptitle,True,True)
		