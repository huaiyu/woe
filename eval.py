# -*- coding:utf-8 -*-
__author__ = 'boredbird'
import pandas as pd
import numpy as np
import scipy
import matplotlib.pyplot as plt

def eval_feature_detail(Info_Value_list,out_path=False):
    """
    format InfoValue list to Dataframe
    :param Info_Value_list: Instance list of Class InfoValue
    :param out_path:specify the Dataframe to csv file path ,default False
    :return:DataFrame about feature detail
    """
    rst = Info_Value_list
    format_rst = []

    for kk in range(0,len(rst)):
        print  rst[kk].var_name
        split_list = []
        if rst[kk].split_list != []:
            if not rst[kk].is_discrete:
                #deal with split_list
                split_list.append('(-INF,'+str(rst[kk].split_list[0])+']')
                for i in range(0,len(rst[kk].split_list)-1):
                    split_list.append('(' + str(rst[kk].split_list[i])+','+ str(rst[kk].split_list[i+1]) + ']')

                split_list.append('(' + str(rst[kk].split_list[len(rst[kk].split_list)-1]) + ',+INF)')
            else:
                split_list = rst[kk].split_list
        else:
            split_list.append('(-INF,+INF)')

        # merge into dataframe
        columns = ['var_name','split_list','sub_total_sample_num','positive_sample_num'
            ,'negative_sample_num','sub_total_num_percentage','positive_rate_in_sub_total'
            ,'woe_list','iv_list','iv']
        rowcnt = len(rst[kk].iv_list)
        var_name = [rst[kk].var_name] * rowcnt
        iv = [rst[kk].iv] * rowcnt
        iv_list = rst[kk].iv_list
        woe_list = rst[kk].woe_list
        a = pd.DataFrame({'var_name':var_name,'iv_list':iv_list,'woe_list':woe_list
                             ,'split_list':split_list,'iv':iv,'sub_total_sample_num':rst[kk].sub_total_sample_num
                             ,'positive_sample_num':rst[kk].positive_sample_num,'negative_sample_num':rst[kk].negative_sample_num
                             ,'sub_total_num_percentage':rst[kk].sub_total_num_percentage
                             ,'positive_rate_in_sub_total':rst[kk].positive_rate_in_sub_total
                             ,'negative_rate_in_sub_total':rst[kk].negative_rate_in_sub_total},columns=columns)
        format_rst.append(a)

    # merge dataframe list into one dataframe vertically
    cformat_rst = pd.concat(format_rst)

    if out_path:
        file_name = out_path if isinstance(out_path, str) else None
        cformat_rst.to_csv(file_name, index=False)

    return cformat_rst


def eval_data_summary(df_list,source_name,out_path=False):
    '''
    :param df_list: A dataset DataFrame
    :param source_name: string type
    :param out_path: specify the Dataframe to csv file path ,default False
    :return: DataFrame about dataset summary info
    '''
    train_validation_data_summary = []
    for i in range(len(source_name)):
        a = dict()
        a['source'] = source_name[i]
        a['total_sample_cnt'] = len(df_list[i])
        a['positive_sample_cnt'] = df_list[i]['target'].sum()
        a['negative_sample_cnt'] = a['total_sample_cnt'] - a['positive_sample_cnt']
        a['positive_rate'] = a['positive_sample_cnt']*1.0/a['total_sample_cnt']
        train_validation_data_summary.append(a)

    train_validation_data_summary = pd.DataFrame(train_validation_data_summary)

    if out_path:
        file_name = out_path if isinstance(out_path, str) else None
        train_validation_data_summary.to_csv(file_name, index=False)

    return train_validation_data_summary


def eval_model_summary(list_dict,out_path=False):
    '''
    :param list_dict: a list of dict
    :param out_path: specify the Dataframe to csv file path ,default False
    :return: DataFrame about model summary info
    '''
    model_summary = pd.DataFrame([list_dict[0]])
    if len(list_dict)>1:
        for i in range(len(list_dict)-1):
            b = pd.DataFrame([list_dict[i+1]])
            model_summary = pd.merge(model_summary, b, how='outer')

    if out_path:
        file_name = out_path if isinstance(out_path, str) else None
        model_summary.to_csv(file_name, index=False)

    return model_summary


def wald_test(model,X):
    '''
    :param model: a model file that should have predict_proba() function
    :param X: dataset features DataFrame
    :return: the value of wald_stats,p_value
    '''
    pred_probs = np.matrix(model.predict_proba(X))
    X_design = np.hstack((np.ones(shape=(X.shape[0], 1)), X))
    diag_array = np.multiply(pred_probs[:, 0], pred_probs[:, 1]).A1
    V = scipy.sparse.diags(diag_array)
    m1 = X_design.T * V
    m2 = m1.dot(X_design)
    cov_mat = np.linalg.inv(m2)

    model_params = np.hstack((model.intercept_[0], model.coef_[0]))
    wald_stats = (model_params / np.sqrt(np.diag(cov_mat))) ** 2

    wald = scipy.stats.wald()
    p_value = wald.pdf(wald_stats)

    return wald_stats,p_value


def eval_feature_summary(train_X,model,civ_list,candidate_var_list,out_path=False):
    '''
    :param train_X: training dataset features DataFrame
    :param model: model file
    :param civ_list: list of InfoValue Class instances
    :param candidate_var_list: the list of model input variable
    :param out_path: specify the Dataframe to csv file path ,default False
    :return: DataFrame about feature summary
    '''
    feature_summary = {}
    feature_summary['feature_name'] = list(['Intercept'])
    feature_summary['feature_name'].extend(list(candidate_var_list))
    feature_summary['coef'] = [model.intercept_]
    feature_summary['coef'].extend(model.coef_[0])
    var_name = [civ.var_name for civ in civ_list]
    feature_summary['iv'] = [0]
    feature_summary['iv'].extend([civ_list[var_name.index(var)].iv for var in candidate_var_list])
    feature_summary['wald_stats'], feature_summary['p_value'] = wald_test(model, train_X)

    feature_summary = pd.DataFrame(feature_summary)
    if out_path:
        file_name = out_path if isinstance(out_path, str) else None
        feature_summary.to_csv(file_name, index=False)

    return feature_summary


def eval_segment_metrics(target, predict_proba, segment_cnt = 20,out_path=False):
    '''
    :param target: the list of actual target value
    :param predict_proba: the list of predicted probability
    :param segment_cnt: the segment number
    :param out_path: specify the Dataframe to csv file path ,default False
    :return: DataFrame about segment metrics
    '''
    proba_descend_idx = np.argsort(predict_proba)
    proba_descend_idx = proba_descend_idx[::-1]

    grp_idx = 1
    start_idx = 0
    total_sample_cnt = len(predict_proba)
    total_positive_sample_cnt = target.sum()
    total_negative_sample_cnt = total_sample_cnt - total_positive_sample_cnt

    segment_sample_cnt = int(len(predict_proba) / segment_cnt)
    cumulative_sample_percentage = 0.0
    cumulative_positive_percentage = 0.0
    cumulative_negative_percentage = 0.0

    segment_list = []
    columns = ['grp_idx', 'segment_sample_cnt', 'segment_sample_percentage', 'cumulative_sample_percentage',
               'in_segment_positive_percentage', 'positive_percentage_in_total', 'cumulative_positive_percentage',
               'cumulative_negative_percentage', 'ks']

    while start_idx < total_sample_cnt:
        s = {}
        s['grp_idx'] = grp_idx
        segment_idx_list = proba_descend_idx[start_idx : start_idx + segment_sample_cnt]
        segment_target = target[segment_idx_list]

        segment_sample_cnt = len(segment_idx_list)
        s['segment_sample_cnt'] = segment_sample_cnt

        segment_pos_cnt = segment_target.sum()
        segment_neg_cnt = segment_sample_cnt - segment_pos_cnt

        segment_sample_percentage = segment_sample_cnt*1.0/total_sample_cnt
        s['segment_sample_percentage'] =  segment_sample_percentage

        pos_percentage_in_total = float(segment_pos_cnt * 100) / total_positive_sample_cnt
        neg_percentage_in_total = float(segment_neg_cnt * 100) / total_negative_sample_cnt
        s['positive_percentage_in_total'] = pos_percentage_in_total

        in_segment_positive_percentage = float(segment_pos_cnt) / segment_sample_cnt
        s['in_segment_positive_percentage'] = in_segment_positive_percentage

        cumulative_sample_percentage += segment_sample_percentage
        s['cumulative_sample_percentage'] = cumulative_sample_percentage

        cumulative_positive_percentage += pos_percentage_in_total
        cumulative_negative_percentage += neg_percentage_in_total
        s['cumulative_positive_percentage'] = cumulative_positive_percentage
        s['cumulative_negative_percentage'] = cumulative_negative_percentage

        ks = cumulative_positive_percentage - cumulative_negative_percentage
        s['ks'] = ks

        segment_list.append(s)
        grp_idx += 1
        start_idx += segment_sample_cnt

    segment_list = pd.DataFrame(segment_list,columns=columns)
    if out_path:
        file_name = out_path if isinstance(out_path, str) else None
        segment_list.to_csv(file_name, index=False)

    return segment_list


def eval_model_stability(proba_train, proba_validation, segment_cnt = 10,out_path=False):
    '''
    :param proba_train: the list of predicted probability on training dataset
    :param proba_validation: the list of predicted probability on validation dataset
    :param segment_cnt: the segment number
    :param out_path: specify the Dataframe to csv file path ,default False
    :return: DataFrame about model stability
    '''
    step = 1.0/segment_cnt
    flag = 0.0
    model_stability = []
    len_train = len(proba_train)
    len_validation = len(proba_validation)

    columns = ['score_range','segment_train_percentage','segment_validation_percentage','difference',
               'variance','ln_variance','stability_index']

    while flag < 1.0:
        temp = {}

        score_range = '['+str(flag)+','+str(flag + step)+')'
        segment_train_cnt = proba_train[(proba_train >= flag) & (proba_train < flag + step)].count()
        segment_train_percentage = segment_train_cnt*1.0/len_train
        segment_validation_cnt = proba_validation[(proba_validation >= flag) & (proba_validation < flag + step)].count()
        segment_validation_percentage = segment_validation_cnt * 1.0 / len_validation
        difference = segment_validation_percentage - segment_train_percentage
        variance = float(segment_validation_percentage)/segment_train_percentage
        ln_variance = variance
        stability_index = difference * ln_variance

        temp['score_range'] = score_range
        temp['segment_train_percentage'] = segment_train_percentage
        temp['segment_validation_percentage'] = segment_validation_percentage
        temp['difference'] = difference
        temp['variance'] = variance
        temp['ln_variance'] = ln_variance
        temp['stability_index'] = stability_index

        model_stability.append(temp)
        flag += step

    model_stability = pd.DataFrame(model_stability,columns=columns)
    if out_path:
        file_name = out_path if isinstance(out_path, str) else None
        model_stability.to_csv(file_name, index=False)

    return model_stability

def eval_feature_stability(civ_list, df_train, df_validation,candidate_var_list,out_path=False):
    '''
    :param civ_list: List of InfoValue Class instances
    :param df_train: DataFrame of training dataset
    :param df_validation: DataFrame of validation dataset
    :param candidate_var_list: the list of model input variable
    :param out_path: specify the Dataframe to csv file path ,default False
    :return: DataFrame about features stability
    '''
    psi_dict = {}

    civ_var_list = [civ_list[i].var_name for i in range(len(civ_list))]
    intersection = list(set(civ_var_list).intersection(set(candidate_var_list)))
    civ_idx_list = [civ_var_list.index(var) for var in intersection]

    len_train = len(df_train)
    len_validation = len(df_validation)

    psi_dict['feature_name'] = []
    psi_dict['group'] = []
    psi_dict['segment_train_cnt'] = []
    psi_dict['segment_train_percentage'] = []
    psi_dict['segment_validation_cnt'] = []
    psi_dict['segment_validation_percentage'] = []

    for i in civ_idx_list:
        if civ_list[i].is_discrete:
            for j in range(len(civ_list[i].split_list)):
                psi_dict['feature_name'].append(civ_list[i].var_name)
                psi_dict['group'].append(civ_list[i].split_list[j])

                civ_split_list = civ_list[i].split_list[j]
                segment_train_cnt = 0
                for m in civ_split_list:
                    segment_train_cnt += df_train[civ_list[i].var_name][df_train[civ_list[i].var_name] == m].count()

                psi_dict['segment_train_cnt'].append(segment_train_cnt)
                psi_dict['segment_train_percentage'].append(float(segment_train_cnt)/len_train)

                segment_validation_cnt = 0
                for m in civ_split_list:
                    segment_validation_cnt += df_validation[civ_list[i].var_name][df_validation[civ_list[i].var_name] == m].count()

                psi_dict['segment_validation_cnt'].append(segment_validation_cnt)
                psi_dict['segment_validation_percentage'].append(float(segment_validation_cnt)/len_validation)

        else:
            split_list = []
            split_list.append(float("-inf"))
            split_list.extend([temp for temp in civ_list[i].split_list])
            split_list.append(float("inf"))
            var_name = civ_list[i].var_name

            for j in range(len(split_list)-3):
                psi_dict['feature_name'].append(civ_list[i].var_name)
                psi_dict['group'].append('('+str(split_list[j])+','+str(split_list[j+1])+']')

                segment_train_cnt = df_train[var_name][(df_train[var_name] > split_list[j])&(df_train[var_name] <= split_list[j+1])].count()

                psi_dict['segment_train_cnt'].append(segment_train_cnt)
                psi_dict['segment_train_percentage'].append(float(segment_train_cnt)/len_train)

                segment_validation_cnt = df_validation[var_name][(df_validation[var_name] > split_list[j])&
                                                                    (df_validation[var_name] <= split_list[j+1])].count()

                psi_dict['segment_validation_cnt'].append(segment_validation_cnt)
                psi_dict['segment_validation_percentage'].append(float(segment_validation_cnt)/len_validation)

            psi_dict['feature_name'].append(var_name)
            psi_dict['group'].append('(' + str(split_list[len(split_list)-2]) + ',+INF)')

            segment_train_cnt = df_train[var_name][df_train[var_name] > split_list[len(split_list)-1]].count()
            psi_dict['segment_train_cnt'].append(segment_train_cnt)
            psi_dict['segment_train_percentage'].append(float(segment_train_cnt) / len_train)

            segment_validation_cnt = df_validation[var_name][df_validation[var_name] > split_list[len(split_list)-1]].count()
            psi_dict['segment_validation_cnt'].append(segment_validation_cnt)
            psi_dict['segment_validation_percentage'].append(float(segment_validation_cnt) / len_validation)

    psi_dict['difference'] = pd.Series(psi_dict['segment_validation_percentage']) - pd.Series(psi_dict['segment_train_percentage'])
    psi_dict['variance'] = map(lambda (x, y): x / (y+0.0000001), zip(psi_dict['segment_validation_percentage'], psi_dict['segment_train_percentage']))
    psi_dict['Ln(variance)'] = np.log(psi_dict['variance'])
    psi_dict['stability_index'] = np.dot(psi_dict['difference'],psi_dict['Ln(variance)'])

    columns = ['feature_name','group','segment_train_cnt','segment_train_percentage',
               'segment_validation_cnt','segment_validation_percentage','difference',
               'variance','Ln(variance)','stability_index']

    psi_df = pd.DataFrame(psi_dict, columns=columns)
    if out_path:
        file_name = out_path if isinstance(out_path, str) else None
        psi_df.to_csv(file_name, index=False)

    return psi_df


def plot_ks(pos_percent, neg_percent, file_name=None):
    '''
    pos_percent: 1-d array, cumulative positive sample percentage
    neg_percent: 1-d array, cumulative negative sample percentage
    return:None
    '''
    plt.plot(pos_percent, 'ro-', label="positive")
    plt.plot(neg_percent, 'go-', label="negative")

    plt.grid(True)
    plt.legend(loc=0)
    plt.xlabel("population")
    plt.ylabel("cumulative percentage")

    if file_name is not None:
        plt.savefig(file_name)

    else:
        plt.show()

    plt.close()


def compute_ks_gini(target, predict_proba, segment_cnt=100, plot=False):
    '''
    target: numpy array of shape (1,)
    predict_proba: numpy array of shape (1,), predicted probability of the sample being positive
    segment_cnt: segment count for computing KS score, more segments result in more accurate estimate of KS score, default is 100
    plot: boolean or string, whether to draw the KS plot, save to a file if plot is string of the file name

    returns:
    gini: float, gini score estimation
    ks: float, ks score estimation
    '''

    proba_descend_idx = np.argsort(predict_proba)
    proba_descend_idx = proba_descend_idx[::-1]

    one_segment_sample_num = int(len(predict_proba) / segment_cnt)
    grp_idx = 1
    start_idx = 0
    total_sample_cnt = len(predict_proba)
    total_positive_sample_cnt = target.sum()
    total_negative_sample_cnt = total_sample_cnt - total_positive_sample_cnt

    cumulative_positive_percentage = 0.0
    cumulative_negative_percentage = 0.0
    cumulative_random_positive_percentage = 0.0
    random_positive_percentage_step = 100.0 / segment_cnt
    ks_pos_percent_list = list()
    ks_neg_percent_list = list()
    ks_score = 0.0
    gini_a_area = 0.0

    while start_idx < total_sample_cnt:
        segment_idx_list = proba_descend_idx[start_idx: start_idx + one_segment_sample_num]
        segment_target = target[segment_idx_list]

        segment_sample_cnt = len(segment_idx_list)

        segment_pos_cnt = segment_target.sum()
        segment_neg_cnt = segment_sample_cnt - segment_pos_cnt

        pos_percentage_in_total = float(segment_pos_cnt * 100) / total_positive_sample_cnt
        neg_percentage_in_total = float(segment_neg_cnt * 100) / total_negative_sample_cnt

        cumulative_positive_percentage += pos_percentage_in_total
        cumulative_negative_percentage += neg_percentage_in_total

        ks = cumulative_positive_percentage - cumulative_negative_percentage
        ks_score = max(ks_score, ks)

        cumulative_random_positive_percentage += random_positive_percentage_step

        gini_a_area += (cumulative_positive_percentage - cumulative_random_positive_percentage) * (1.0 / segment_cnt)

        ks_pos_percent_list.append(cumulative_positive_percentage)
        ks_neg_percent_list.append(cumulative_negative_percentage)

        grp_idx += 1
        start_idx += one_segment_sample_num

    gini_score = gini_a_area * 2

    if plot:
        file_name = plot if isinstance(plot, str) else None
        plot_ks(ks_pos_percent_list, ks_neg_percent_list, file_name)

    return (gini_score, ks_score)
