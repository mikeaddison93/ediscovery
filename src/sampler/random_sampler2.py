#!/usr/bin/env python2.7
'''
TODO: (1) Add description ???

Created by: Abhiram J.  
Created On: Jan 28, 2013   

'''
import sys
import os
import math
import random
import argparse
import datetime
import logging
from file_utils import find_files_in_folder, copy_random_files

# PREVALENCE is the likelihood of finding a responsive/positive example in population
# We assume this as 0.5 (most conservative) as we do not know prior information about data
PREVALENCE = 0.5
logger = logging.getLogger('random_sampler_test_function')
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)
ch.setFormatter(formatter)
logger.addHandler(ch)

# input:
# inputFolder/pst = Source of the datasets
# confidence: float between 0 & 1,
# precision: confidence: float between 0 & 1
def main():
	
	
	timestamp = datetime.datetime.now()
	arg_parser = argparse.ArgumentParser('Random sample test function:')
	arg_parser.add_argument("-d", dest="input_folder", type=str,
						    help="the root directory for all the mails",
						    required=True)
	arg_parser.add_argument("-c", dest="confidence", type=float,
						    help="The confidence interval eg. 0.95 for 95%",
						    required=True)
	arg_parser.add_argument("-p", dest="precision", type=float,
						    help="The precision for the interval eg. 0.02 precision for\
						    .95 confidence gives 95%  +/-2% error",
						    required=True)
	arg_parser.add_argument("-o", dest="output_dir", type=str, help="Output directory of samples",
						    default="/home/abhiramj/code/temp/samples",
						    required=False)
	output_folder = arg_parser.parse_args()
	
	if  not os.path.isdir(output_folder.output_dir):
		logger.debug("Making output directory" + output_folder.output_dir)
		os.makedirs(output_folder.output_dir)
	
	file_handle = logging.FileHandler(os.path.join(output_folder.output_dir,'random_sampler_test_function--' +str(timestamp)+'.log'))
	file_handle.setLevel(logging.INFO)
	file_handle.setFormatter(formatter)
	logger.addHandler(file_handle)
	
	logger.info("Args are: ")
	logger.info("input_folder: "+ output_folder.input_folder)
	logger.info("confidence: "+ str(output_folder.confidence))
	logger.info("precision: "+ str(output_folder.precision))
	logger.info("output_dir: "+ output_folder.output_dir)
	

	if not os.path.exists(output_folder.input_folder) :
		logger.error("Exiting with error: Input folder cannot be found")
		raise Exception, "Input folder cannot be found"
	if output_folder.confidence <= 0 or output_folder.confidence > 1:
		logger.error("Exiting with error: Confidence is not valid, enter as a probability between 0 and 1")
		raise Exception, "Confidence is not valid, enter as a probability between 0 and 1"
	if output_folder.precision <= 0 or output_folder.precision > 1:
		logger.error( "Exiting with error: Precision is not valid, enter as a probability between 0 and 1")
		raise Exception, "Precision is not valid, enter as a probability between 0 and 1"


	file_list = find_files_in_folder(output_folder.input_folder)
	message_random_sample = random_sampler(file_list,output_folder.confidence,output_folder.precision,SEEDCONSTANT=0.5)
	
	
	file_destination_dir = output_folder.output_dir +"--"+ str(timestamp)
	copy_random_files(file_destination_dir,message_random_sample)
	return message_random_sample





# SEEDCONSTANT unused currently
def random_sampler(message_id_list, confidence, precision, SEEDCONSTANT):
	'''Description ??
	TODO: Add function details (see 'the tm package' files)
	
	Returns: 
		???
	Arguments: 
		???
	'''
	
	# Uncomment to test sample size of big numbers and verify
	# message_id_list = xrange(10000)
	random.seed(SEEDCONSTANT)

	# setting up z , the diction of confidence -> zvalues
	z = {}
	z[0.999] = 3.3
	z[0.99] =2.577
	z[0.985] =2.43
	z[0.975] = 2.243
	z[0.95]= 1.96
	z[0.90] =1.645
	z[0.85] = 1.439
	z[0.75] = 1.151




	# check that the confidence interval is supported
	if confidence in z:
		# sample size formula based on infinite population
		sample_size= pow(z[confidence],2)*(PREVALENCE)*(1-PREVALENCE)/(pow(precision,2))

		# correction for finite size
		corrected_sample_size = sample_size/(1 + (sample_size-1)/len(message_id_list))
		corrected_sample_size = int(math.ceil(corrected_sample_size))
		logger.info("Sample size is " + str(corrected_sample_size))
		print "Sample size is " + str(corrected_sample_size)
		random_sample = random.sample(message_id_list,corrected_sample_size)
		return random_sample
	else:
		logger.debug("Exiting with reason: Confidence interval not supported")
		raise Exception, "Confidence interval not supported"
		sys.exit(1)


# Standard boilerplate to call the main() function to begin
# the program.
if __name__ == '__main__':
	main()