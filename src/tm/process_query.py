#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''
This script process any given text query  
and finds similar documents from a learned 
topic model.  

Dependency: 
    Gensim package
        
Created On: May 21, 2013
Created By: Clint P. George 
'''


import logging, gensim
import numpy as np
from scipy.spatial.distance import cosine
from utils.utils_email import whitespace_tokenize


logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.ERROR)

def sparse_to_dense(length, tuples_list):
    dense_vec = np.zeros(length)
    for idx, value in tuples_list:
        dense_vec[idx] = value
    return dense_vec


#def cos(v1, v2):
#    return np.dot(v1, v2) / (np.sqrt(np.dot(v1, v1)) * np.sqrt(np.dot(v2, v2)))



    



def load_dictionary(dictionary_file):
    '''This function loads the corpus dictionary 
    
    Returns: 
        a tuple of dictionary
    Arguments:
        dictionary_file - the dictionary file name 

    '''

    return gensim.corpora.Dictionary().load(dictionary_file)


def get_tfidf_mdl(ldac_file, ):
            
    # loads the corpus 
    
    corpus = gensim.corpora.BleiCorpus(ldac_file)
    
    # runs the LSA inference
    
    tfidf = gensim.models.TfidfModel(corpus) 
    corpus_tfidf = tfidf[corpus]
    
    return corpus_tfidf

'''
************************ LDA ****************************
'''    

def load_lda_variables(lda_mdl_file, lda_index_file):
    '''This function loads all the LDA model variables
    
    Returns: 
        lda model, and lda index
    Arguments:
        lda_mdl_file - the LDA model file 
        lda_index_file - the LDA index file 
    '''

    lda = gensim.models.ldamodel.LdaModel.load(lda_mdl_file)
    index = gensim.similarities.MatrixSimilarity.load(lda_index_file)

    return (lda, index)

def get_lda_query_td(doc_text, lda_dictionary, lda_mdl):
    '''Tokenize the input query and returns its topic 
    distributions using the learned LDA model
    
    Returns:
        topic distribution 
    Arguments:
        doc_text - the document in text format 
        lda_dictionary - the dictionary object 
        lda_mdl - the LDA model object 
    
    '''
    # process the query 
    
    query_vec = lda_dictionary.doc2bow(whitespace_tokenize(doc_text))
    
    if len(query_vec) == 0: 
        logging.exception('Query words are not in the dictionary. Exiting topic search!')
        return [] 
    else: 
        logging.info('%d query words are in the dictionary.', len(query_vec))
    
    query_td = lda_mdl[query_vec]
    
    return query_td


def get_lda_query_td2(doc_text, lda_dictionary, lda_beta):
    '''Tokenize the input query and returns its topic 
    distributions using the learned LDA model
    
    Returns:
        topic distribution 
    Arguments:
        doc_text - the document in text format 
        lda_dictionary - the dictionary object 
        lda_beta - the LDA model's beta matrix  
    
    '''
    # process the query 
    
    query_vec = lda_dictionary.doc2bow(whitespace_tokenize(doc_text))
    
    if len(query_vec) == 0: 
        logging.exception('Query words are not in the dictionary. Exiting topic search!')
        return [] 
    else: 
        logging.info('%d query words are in the dictionary.', len(query_vec))
    
    query_term_theta2 = np.array([lda_beta[:,vocab_id] * count for (vocab_id, count) in query_vec]).sum(axis=0)
    query_term_theta2 /= sum(query_term_theta2.tolist()) # normalizes
    query_td2 = [(idx, val) for idx, val in enumerate(query_term_theta2)] 
    
    return query_td2



def compute_topic_similarities(doc_text, src_docs, lda_dictionary, lda_mdl, lda_num_topics):
    '''Tokenize the document and finds document similarities between
    the given document and the documents listed, based on topic modeling 
    and cosine distance 
    
    Returns:
        topic distribution 
    Arguments:
        doc_text - the document in text format 
        lda_dictionary - the dictionary object 
        lda_mdl - the LDA model object 
        lda_num_topics - the number topics in the LDA model 
    
    '''
    # process the query 
    
    query_vec = lda_dictionary.doc2bow(whitespace_tokenize(doc_text))
    query_td = lda_mdl[query_vec]
    qtd_vec = sparse_to_dense(lda_num_topics, query_td)
    
    print 'Query:', ' '.join(whitespace_tokenize(doc_text))
    print 'Number of vocabulary tokens:', len(query_vec)
    print 'Query vector:', query_vec
    print 'Query td:', query_td
    print 'doc_name, cosine, rating, doc_td'
    
    dest_docs = []
    for sdoc in src_docs:
        sdoc_text = sdoc[5]
        sdoc_vec = lda_dictionary.doc2bow(whitespace_tokenize(sdoc_text))
        sdoc_td = lda_mdl[sdoc_vec]
        std_vec = sparse_to_dense(lda_num_topics, sdoc_td)
        cosine_dist = cosine(qtd_vec, std_vec) # ranges from -1 to 1 
        sdoc.append(cosine_dist) # append the cosine distance to the end 
        print sdoc[1], cosine_dist, sdoc[-2], sdoc_td # file_id, cosine, user rating, doc topic distribution 
        dest_docs.append(sdoc)
        
    return dest_docs


def get_lda_topic_dist(docs, lda_dictionary, lda_mdl, num_topics):
    
    doc_tds = [] 
    for doc in docs: 
        doc_vec = lda_dictionary.doc2bow(whitespace_tokenize(doc))
        doc_tds.append(lda_mdl[doc_vec])
    
    num_docs = len(doc_tds)
    theta_matrix = np.zeros((num_docs, num_topics))
    count = 0
    for doc in doc_tds: 
        doc = dict(doc)
        theta_matrix[count, doc.keys()] = doc.values()
        count += 1 

    return theta_matrix


def print_lda_topics_on_entropy(lda_mdl, file_name='topic-words.csv', topn=50):
    '''
    This function loads the LDA model, computes the entropy 
    of all topics, and sort and display them in the increasing 
    order of entropy    
    
    '''
    import math
    
    topics = lda_mdl.show_topics(topics=-1, topn=topn, log=False, formatted=False)
    
    # Computes topic-entropy 
    topic_entropy = []
    for topic in topics: 
        entropy = 0.0 
        for (prob, _) in topic:
            entropy += prob * math.log(prob) 
        topic_entropy.append(-entropy)
        
    # Gets the sorted index in the ascending order of topic-entropy  
    sort_index = sorted(range(len(topic_entropy)),key=topic_entropy.__getitem__)
    
    print '---------------------------------------------------------------------'
    print 'LDA topics:'
    print 
     
    with open(file_name, 'w') as fp:
        for idx in sort_index:
            topic = topics[idx] 
            terms = u','.join(['%s(%.8f)' % (term, prob) for (prob, term) in topic])
            out_line = u','.join(['%.8f' % topic_entropy[idx], terms]) 
            print out_line
            print >>fp, out_line   
    
    print '---------------------------------------------------------------------'



def print_dominant_query_topics(query_td, lda_mdl, TOP_K_TOPICS = 5):
    from operator import itemgetter
    import heapq
    
    dominant_topics = heapq.nlargest(TOP_K_TOPICS, dict(query_td).items(), key=itemgetter(1))
    
    # print 'Query distribution:', query_td
    print 'Top %s query topic(s):' % min(TOP_K_TOPICS, len(query_td)), dominant_topics
    topic_words = lda_mdl.show_topics(topics=-1, topn=20, log=False, formatted=False)
    for (topic_id, _) in dominant_topics:
        print '\t topic #%d:' % topic_id, 
        for (prob, term) in topic_words[topic_id] :
            print term, '(%.5f),' % prob, 
        print 
    print  
        
def get_dominant_query_topics(query_text, lda_dictionary, lda_mdl, TOP_K_TOPICS = 5):
    '''Tokenize the input query and finds the top K dominant query 
    topics from an LDA model 
    
    Returns:
        dominant_topics - a tuple list of (topic_id, topic_prob)
    Arguments:
        query_text - the query in text format 
        lda_dictionary - the dictionary object 
        lda_mdl - the LDA model object 
    
    '''
    from operator import itemgetter
    import heapq
    
    # process the query 
    
    query_vec = lda_dictionary.doc2bow(whitespace_tokenize(query_text))
    
    if len(query_vec) == 0: 
        logging.exception('Query words are not in the dictionary. Exiting topic search!')
        return [] 
    else: 
        logging.info('%d query words are in the dictionary.', len(query_vec))
    
    query_td = lda_mdl[query_vec]

    print 'Query TF:', [(w_id, lda_dictionary[w_id], count) for (w_id, count) in query_vec]
    print_dominant_query_topics(query_td, lda_mdl, TOP_K_TOPICS)
   
    dominant_topics = heapq.nlargest(TOP_K_TOPICS, dict(query_td).items(), key=itemgetter(1))

    return dominant_topics # (topic_id, topic_prob)  

def get_query_top_topic_idx(query_td, lda_mdl, TOP_K_TOPICS = 5):
    '''Tokenize the input query and finds the top K dominant query 
    topics from an LDA model 
    
    Returns:
        dominant_topics - a tuple list of (topic_id, topic_prob)
    Arguments:
        query_td - the query topic distribution 
        lda_mdl - the LDA model object 
    
    '''
    from operator import itemgetter
    import heapq
    
    print_dominant_query_topics(query_td, lda_mdl, TOP_K_TOPICS)
   
    dominant_topics = heapq.nlargest(TOP_K_TOPICS, dict(query_td).items(), key=itemgetter(1)) # (topic_id, topic_prob)  
    dominant_topics_idx = [idx for (idx, _) in dominant_topics] # get the topic indices 
    
    return dominant_topics_idx 

def search_lda_model(query_text, lda_dictionary, lda_mdl, lda_index, lda_file_path_index, limit):
    '''Tokenize the input query and finds topically 
    similar documents (responsive) using the LDA based 
    document search. 
    
    Returns:
        responsive_docs - [doc_id, doc_dir_path, doc_name, score] 
    Arguments:
        query_text - the query in text format 
        lda_dictionary - the dictionary object 
        lda_mdl - the LDA model object 
        lda_index - the index object 
        lda_file_path_index - the list of file details 
        limit - the limit on the number of responsive records 
    
    '''
    
    # process the query 
    
    query_vec = lda_dictionary.doc2bow(whitespace_tokenize(query_text))
    
    if len(query_vec) == 0: 
        logging.exception('Query words are not in the dictionary. Exiting topic search!')
        return [] 
    else: 
        logging.info('%d query words are in the dictionary.', len(query_vec))
    
    query_td = lda_mdl[query_vec]
    
    # querying based on cosine distance
    
    sims = lda_index[query_td] # perform a similarity query against the corpus
    sims = sorted(enumerate(sims), key=lambda item: -item[1])
    
    ## Identifies responsive documents
     
    responsive_docs_idx = sims[0:limit]
    responsive_docs = [] 
    for (doc_id, score) in responsive_docs_idx: 
        doc = list(lda_file_path_index[doc_id]) # i.e., [doc_id, doc_dir_path, doc_name]
        doc.append(score)
        responsive_docs.append(doc)
    
    return responsive_docs
    
def search_lda_model2(query_td, lda_index, lda_file_path_index, limit):
    '''Tokenize the input query and finds topically 
    similar documents (responsive) using the LDA based 
    document search. 
    
    Returns:
        responsive_docs - [doc_id, doc_dir_path, doc_name, score] 
    Arguments:
        query_td - the query topic distribution  
        lda_index - the index object 
        lda_file_path_index - the list of file details 
        limit - the limit on the number of responsive records 
    
    '''
    
    # querying based on cosine distance
    
    sims = lda_index[query_td] # perform a similarity query against the corpus
    sims = sorted(enumerate(sims), key=lambda item: -item[1])
    
    ## Identifies responsive documents
     
    responsive_docs_idx = sims[0:limit]
    responsive_docs = [] 
    for (doc_id, score) in responsive_docs_idx: 
        doc = list(lda_file_path_index[doc_id]) # i.e., [doc_id, doc_dir_path, doc_name]
        doc.append(score)
        responsive_docs.append(doc)
    
    return responsive_docs
    
    
'''
************************ LSA ****************************
'''   


def load_lsi_variables(lsi_mdl_file, lsi_index_file):
    '''This function loads all the lsi model variables
    
    Returns: 
        lsi model, and lsi index
    Arguments:
        lsi_mdl_file - the LSI model file 
        lsi_index_file - the LSI index file 
    '''

    lsi = gensim.models.lsimodel.LsiModel.load(lsi_mdl_file)
    index = gensim.similarities.MatrixSimilarity.load(lsi_index_file)

    return (lsi, index)



def search_lsi_model(query, dictionary, lsi, index, files_info, limit=5):
    '''Tokenize the input query and finds topically 
    similar documents (responsive) using lsi based 
    document search. 
    
    Returns:
        a lists of lists of responsive document details,
        i.e., [doc_id, doc_dir_path, doc_name, score] 
    Arguments:
        query - the query in text format 
        dictionary - the dictionary object 
        lsi - the lsi model object 
        index - the index object 
        files_info - the list of file details 
        limit - the limit on the number of responsive records 
    
    '''

    # process the query 
    
    query_vec = dictionary.doc2bow(whitespace_tokenize(query))
    if len(query_vec) == 0: 
        logging.exception('Query words are not in the dictionary. Exiting topic search!')
        return [] 
    else: 
        logging.info('%d query words are in the dictionary.', len(query_vec)) 
    
    
    query_td = lsi[query_vec]
    
    # print 'Query vector      :', [(w_id, dictionary[w_id], count) for (w_id, count) in query_vec]
    # print 'Query distribution:', query_td
    
    # querying based on cosine distance
    
    sims = index[query_td] # perform a similarity query against the corpus
    sims = sorted(enumerate(sims), key=lambda item: -item[1])
    
    ## Identifies responsive and non-responsive documents
     
    responsive_docs_idx = sims[0:limit]
    
    responsive_docs = [] 
    for (doc_id, score) in responsive_docs_idx: 
        doc = list(files_info[doc_id]) # i.e., [doc_id, doc_dir_path, doc_name]
        doc.append(score)
        responsive_docs.append(doc)
    
    return responsive_docs




'''
************************ MAIN ****************************
'''   

if __name__ == '__main__':
    pass