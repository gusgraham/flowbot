from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt
from datetime import datetime
from flowbot_data_classification import dataClassification

from flowbot_data_classification import *

from ui_elements.ui_flowbot_dialog_data_classification_base import Ui_Dialog


class flowbot_dialog_data_classification(QtWidgets.QDialog, Ui_Dialog):
    outputFileSpec = ""
    trainingDataFileSpec = resource_path("resources\\training_data_3.csv")
    aDataClassification = None

    def __init__(self, aDC, parent=None):
        """Constructor."""
        super(flowbot_dialog_data_classification, self).__init__(parent)
        self.setupUi(self)

        self.aDataClassification = aDC
        self.btnOK.clicked.connect(self.onAccept)
        self.btnCancel.clicked.connect(self.onReject)
        self.btnTrainingData.clicked.connect(self.openTrainingData)
        self.chkFullPeriod.clicked.connect(self.enableButtons)

        self.chkBootstrap.setCheckState(
            Qt.Checked) if self.aDataClassification.blnBootstrap else self.chkBootstrap.setCheckState(Qt.Unchecked)
        self.edtMaxDepth.setText(self.aDataClassification.strMaxDepth)
        self.edtMinSamplesLeaf.setText(
            self.aDataClassification.strMinSamplesLeaf)
        self.edtMinSamplesSplit.setText(
            self.aDataClassification.strMinSamplesSplit)
        self.edtN_Estimators.setText(self.aDataClassification.strN_Estimators)
        self.edtMaxFeatures.setText(self.aDataClassification.strMaxFeatures)
        self.trainingDataFileSpec = self.aDataClassification.strTrainingDataFileSpec
        self.edtTrainingDataSpec.setText(self.trainingDataFileSpec)
        self.chkFullPeriod.setCheckState(
            Qt.Checked) if self.aDataClassification.blnFullPeriod else self.chkFullPeriod.setCheckState(Qt.Unchecked)
        self.dteStartDate.setMinimumDateTime(
            self.aDataClassification.classifiedFMs.classEarliestStart)
        self.dteStartDate.setMaximumDateTime(
            self.aDataClassification.classifiedFMs.classLatestEnd)
        self.dteEndDate.setMinimumDateTime(
            self.aDataClassification.classifiedFMs.classEarliestStart)
        self.dteEndDate.setMaximumDateTime(
            self.aDataClassification.classifiedFMs.classLatestEnd)
        self.enableButtons()

    def onAccept(self):

        self.aDataClassification.blnBootstrap = self.chkBootstrap.isChecked()
        self.aDataClassification.strMaxDepth = self.edtMaxDepth.text()
        self.aDataClassification.strMinSamplesLeaf = self.edtMinSamplesLeaf.text()
        self.aDataClassification.strMinSamplesSplit = self.edtMinSamplesSplit.text()
        self.aDataClassification.strN_Estimators = self.edtN_Estimators.text()
        self.aDataClassification.strMaxFeatures = self.edtMaxFeatures.text()
        self.aDataClassification.strOutputFileSpec = self.outputFileSpec
        self.aDataClassification.strTrainingDataFileSpec = self.trainingDataFileSpec

        if not self.chkFullPeriod.isChecked():
            self.aDataClassification.blnFullPeriod = False
            # self.aDataClassification.class_date_range_start = datetime.strptime(
            #     self.dteStartDate.dateTime().toPyDateTime(), '%d/%m/%Y')
            # self.aDataClassification.class_date_range_end = datetime.strptime(
            #     self.dteEndDate.dateTime().toPyDateTime(), '%d/%m/%Y')
            self.aDataClassification.class_date_range_start = datetime.strptime(
                self.dteStartDate.dateTime().toPyDateTime(), '%d/%m/%Y')
            self.aDataClassification.class_date_range_end = datetime.strptime(
                self.dteEndDate.dateTime().toPyDateTime(), '%d/%m/%Y')
        else:
            self.aDataClassification.blnFullPeriod = True
            self.aDataClassification.class_date_range_start = '1/1/1066'
            self.aDataClassification.class_date_range_end = '9/9/9999'

        if self.matchDefaultParams():
            self.aDataClassification.useDefaultParams = True
        else:
            self.aDataClassification.useDefaultParams = False

        self.accept()

    def onReject(self):
        self.reject()

    def matchDefaultParams(self):

        testRA = dataClassification()

        if (testRA.blnBootstrap == self.chkBootstrap.isChecked() and
            testRA.strMaxDepth == self.edtMaxDepth.text() and
            testRA.strMinSamplesLeaf == self.edtMinSamplesLeaf.text() and
            testRA.strMinSamplesSplit == self.edtMinSamplesSplit.text() and
            testRA.strN_Estimators == self.edtN_Estimators.text() and
            testRA.strMaxFeatures == self.edtMaxFeatures.text() and
                testRA.blnFullPeriod == self.chkFullPeriod.isChecked()):
            return True
        else:
            return False

    def enableButtons(self):

        if self.chkFullPeriod.isChecked():
            self.dteStartDate.setReadOnly(True)
            self.dteEndDate.setReadOnly(True)
        else:
            self.dteStartDate.setReadOnly(False)
            self.dteEndDate.setReadOnly(False)

    def openTrainingData(self):
        fileSpec, filter = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open Data Classification Training Data...", "", 'CSV Files (*.csv)')
        if len(fileSpec) == 0:
            return
        else:
            self.edtTrainingDataSpec.setText(fileSpec)
            self.trainingDataFileSpec = fileSpec

    # def flow_survey_data_classification(self):
    #
        # class_start_time = datetime.now()
        # dateformat = '%d/%m/%Y'
        #
        # if not self.chkFullPeriod.isChecked():
            # class_date_range_start = datetime.strptime(self.dteStartDate.dateTime().toPyDateTime(), dateformat)
            # class_date_range_end =  datetime.strptime(self.dteEndDate.dateTime().toPyDateTime(), dateformat)
        # else:
            # class_date_range_start = '1/1/1066'
            # class_date_range_end =  '9/9/9999'
            #
        # bootstrap_val = self.chkBootstrap.isChecked()
        # max_depth_val = int(self.edtMaxDepth.text())
        # min_samples_leaf_val= int(self.edtMinSamplesLeaf.text())
        # min_samples_split_val= int(self.edtMinSamplesSplit.text())
        # n_estimators_val = int(self.edtN_Estimators.text())
        #
        # if self.edtMaxFeatures.text() == 'auto':
            # max_features_val= self.edtMaxFeatures.text()
        # else:
            # max_features_val= int(self.edtMaxFeatures.text())
            #
            #
        # data_columns=['monitor_name','day','max_depth','min_depth','ave_depth','std_dev_depth','zero_depth','max_velocity','min_velocity','ave_velocity','std_dev_velocity','zero_velocity']
        #
        # data_df = pd.DataFrame(columns=data_columns)
        #
        # output_path = self.outputFileSpec
        #
        # training_path = self.trainingDataFileSpec
        #
        # total_m = len(self.aDataClassification.classifiedFMs.classFMs)
        #
        # m_list = ['FM', 'DM']
        #
        # no_data_list = []
        #
        # y = 0
        #
        # data_df = data_df.iloc[0:0]
        #
        # for fm in self.aDataClassification.classifiedFMs.classFMs.values():
        #
            # FDV_zip_list_dates = []
            # FDV_zip_list_days = []
            # for i in range(len(fm.dateRange)):
            #
            # FDV_zip_list_dates.append(fm.dateRange[i].strftime("%d/%m/%Y %H:%M"))
            #
            # FDV_zip_list_days.append(fm.dateRange[i].strftime("%d/%m/%Y"))
            #
            # FDV_zip_list =list(zip(FDV_zip_list_dates,FDV_zip_list_days,fm.flowDataRange, fm.depthDataRange, fm.velocityDataRange))
            #
            # FDV_dataframe = pd.DataFrame(FDV_zip_list, columns=['Date', 'Day', 'Flow', 'Depth', 'Velocity'])
            #
            # #__________________________________________________
            #
            # list_of_days = []
            #
            # list_of_days = list(set(FDV_zip_list_days))
            #
            # list_of_flow = []
            # list_of_depth = []
            # list_of_velocity = []
            # zero_depth = 0
            # zero_velocity = 0
            # std_dev_depth = 0
            # std_dev_velocity = 0
            # ave_depth = 0
            # ave_velocity = 0
            #
            # for i in range(len(list_of_days)):
            #
            # if datetime.strptime(class_date_range_start, "%d/%m/%Y") <= datetime.strptime(list_of_days[i], "%d/%m/%Y") <= datetime.strptime(class_date_range_end, "%d/%m/%Y"):
        # #________________________________________________________________________________________________________________
        #
            # day = list_of_days[i]
            #
            # day_variable = FDV_dataframe['Day'] == day
            #
            # day_df = FDV_dataframe[day_variable]
            #
            # list_of_depth = day_df['Depth'].tolist()
            #
            # list_of_velocity = day_df['Velocity'].tolist()
            #
            # #This allows for days that arnt installed for a full day to utilise the zero stats
            # norm_factor = 720/len(list_of_depth)
            #
            # zero_depth = list_of_depth.count(0.0) * norm_factor
            #
            # zero_velocity = list_of_velocity.count(0.0) * norm_factor
            #
            # if int(len(list_of_depth))>5:
            #
            # max_depth =(max(list_of_depth))
            # min_depth =(min(list_of_depth))
            # std_dev_depth = (statistics.stdev(list_of_depth))
            # ave_depth = mean(list_of_depth)
            #
            # max_velocity =(max(list_of_velocity))
            # min_velocity =(min(list_of_velocity))
            # std_dev_velocity = (statistics.stdev(list_of_velocity))
            # ave_velocity = mean(list_of_velocity)
            #
            # #print (monitor_name.rstrip(), day, max_depth, min_depth, ave_depth, std_dev_depth ,zero_depth, max_velocity, min_velocity, ave_velocity, std_dev_velocity,zero_velocity)
            #
            # data_df=data_df.append({'monitor_name': fm.monitorName,'day': day,'max_depth':max_depth,'min_depth':min_depth,'ave_depth':ave_depth,'std_dev_depth':std_dev_depth,'zero_depth':zero_depth,'max_velocity':max_velocity,'min_velocity':min_velocity,'ave_velocity':ave_velocity,'std_dev_velocity':std_dev_velocity,'zero_velocity':zero_velocity}, ignore_index=True)
            #
            # #----------------------------------------------------------------------------
            # #This allows for monitors that have no data yet to be addded to output SS
# #
            # # if len(list_of_depth) == 0:
            # #
            # # print('NO DATA')
            # #
            # # if len(monitor_name.rstrip()) > 0:
            # # no_data_list.append(monitor_name.rstrip())
            #
            # #----------------------------------------------------------------------------
            #
        # #---------------------------------------------------------------------------
        # #This is append the data exracted from the FDV files into 1 df for FM & DM
        #
        # m_type = 'FM' #Just using FMs at the moment
        #
        # if m_type == 'FM':
            # data_df_2 = data_df.copy()
        # elif  m_type == 'DM':
            # data_df_2 = data_df_2.append(data_df, ignore_index=True)
            #
        # balance_data = pd.read_csv(training_path,sep= ',', header=0 )
        #
        # M_variable = balance_data['m_type'] == m_type
        # training_df = balance_data[M_variable]
        #
        # if  m_type == 'FM':
        #
            # X_train = training_df.values[:, 5:15]
            # y_train = training_df.values[:,4]
            #
            # X_test = data_df.iloc[:, 2:12].values.tolist()
            #
        # elif m_type == 'DM':
        #
            # X_train = training_df.values[:, 5:10]
            # y_train = training_df.values[:,4]
            #
            # X_test = data_df.iloc[:, 2:7].values.tolist()
            #
        # if len(X_train)>0 and len(y_train)>0 and len(X_test)>0:
        #
            # #_____________________________________________________________________________________________________________________________________________
            # #This is the classifier
            # rf = RandomForestClassifier(bootstrap = bootstrap_val, max_depth=max_depth_val, max_features =max_features_val, min_samples_leaf = min_samples_leaf_val, min_samples_split = min_samples_split_val, n_estimators=n_estimators_val, random_state=1234567)
            # rf.fit(X_train, y_train)
            # y_pred_rf = rf.predict(X_test)
            # #_____________________________________________________________________________________________________________________________________________
            # #This is the generation of the prediction probabilities
            # class_names =rf.classes_.tolist()
            # predictions = rf.predict_proba(X_test)
            # #_____________________________________________________________________________________________________________________________________________
            # #This is the tabulation of the classifier output and prediction probabilities
            #
            # if m_type == 'FM':
            #
            # fm_df=pd.DataFrame({'FM':data_df['monitor_name'], 'Day':data_df['day'],'Predicted_rf':y_pred_rf,
            # class_names[0]:predictions[:,0],
            # class_names[1]:predictions[:,1],
            # class_names[2]:predictions[:,2],
            # class_names[3]:predictions[:,3],
            # class_names[4]:predictions[:,4],
            # class_names[5]:predictions[:,5],
            # class_names[6]:predictions[:,6],
            # class_names[7]:predictions[:,7],
            # class_names[8]:predictions[:,8],
            # class_names[9]:predictions[:,9],
            # class_names[10]:predictions[:,10],
            # class_names[11]:predictions[:,11],
            # class_names[12]:predictions[:,12]})
            #
            # fm_df=fm_df[['FM', 'Day','Predicted_rf',class_names[0],class_names[1],class_names[2],class_names[3],class_names[4],class_names[5],
            # class_names[6],
            # class_names[7],
            # class_names[8],
            # class_names[9],
            # class_names[10],
            # class_names[11],
            # class_names[12]]]
            #
            # elif m_type == 'DM':
            #
            # dm_df=pd.DataFrame({'FM':data_df['monitor_name'], 'Day':data_df['day'],'Predicted_rf':y_pred_rf,
            # class_names[0]:predictions[:,0],
            # class_names[1]:predictions[:,1],
            # class_names[2]:predictions[:,2]})
            #
            # dm_df=dm_df[['FM', 'Day','Predicted_rf',class_names[0],class_names[1],class_names[2]]]
# #
        # # self.pval = self.pval + 0.5
        # # self.progressbar['value'] = self.pval
        # # self.progressbar.update_idletasks()
        # #_____________________________________________________________________________________________________________________________________________
        # #This process adds the monitor failure events identified from the data classification, if chosen to be added.
        #
        # #if len(self.data_class_FM_multi_List_Box.curselection())>0 and len(self.data_class_DM_multi_List_Box.curselection())>0:
        # # if len(self.data_class_FM_multi_List_Box.curselection())>0 and len(self.data_class_DM_multi_List_Box.curselection())>0:
            # # join_df =pd.concat([dm_df,fm_df], axis=0, ignore_index=True)
            # #
        # # elif len(self.data_class_FM_multi_List_Box.curselection())>0 and len(self.data_class_DM_multi_List_Box.curselection())<=0:
        #
        # join_df = fm_df.copy()
        #
        # # elif len(self.data_class_FM_multi_List_Box.curselection())<=0 and len(self.data_class_DM_multi_List_Box.curselection())>0:
        # #
            # # join_df = dm_df.copy()
            #
        # FM = join_df['FM']
        # Day = join_df['Day']
        # Predicted_rf = join_df['Predicted_rf']
        #
        # join_df.drop(labels=['FM'], axis=1,inplace = True)
        # join_df.drop(labels=['Day'], axis=1,inplace = True)
        # join_df.drop(labels=['Predicted_rf'], axis=1,inplace = True)
        #
        # join_df.insert(0, 'FM', FM)
        # join_df.insert(1, 'Day', Day)
        # join_df.insert(2, 'Predicted_rf', Predicted_rf)
        #
        # concec_df = join_df.copy()
        # concec_df = concec_df.iloc[:, [0, 1, 2]]
        #
        # concec_df['Day'] = concec_df['Day'].apply(lambda x: datetime.strptime(x, "%d/%m/%Y") )
        #
        # concec_df.sort_values(['FM', 'Day'], ascending=[True, True], inplace=True)
        #
        # labels = (concec_df.Predicted_rf  != concec_df.Predicted_rf .shift() ).cumsum()
        #
        # concec_df['flag'] = (labels.map(labels.value_counts()) >= 1 ).astype(int)
        #
        # concec_df = concec_df.loc[(concec_df['flag'] == 1) & (concec_df['Predicted_rf'] == 'X')]
        #
        # # if self.events_class.get() == 1:
        #
        # if self.chkLoadMonitorFailure.isChecked():
        #
            # t=1
            #
            # for i in range(0, len(concec_df)):
            #
            # if concec_df.iloc[i]['Day']-timedelta(days=1) != concec_df.iloc[i-1]['Day'] or i == 0:
            #
            # start = concec_df.iloc[i]['Day']-timedelta(days=2)
            #
            # start_zoom = datetime.strptime(str(start), '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M:%S')
            #
            #
            # for z in range(i, len(concec_df)):
            #
            # if z == len(concec_df)-1 or concec_df.iloc[z]['Day']+ timedelta(days=1) != concec_df.iloc[z+1]['Day'] :
            #
            # end = concec_df.iloc[z]['Day']+timedelta(days=2)
            #
            # end_zoom = datetime.strptime(str(end), '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M:%S')
            #
            # self.tree.insert("" , 0, text= 'X_' + concec_df.iloc[i]['FM']+'-'+str(t), values=(start_zoom,end_zoom))
            #
            # t+=1
            #
            # break
        # #_____________________________________________________________________________________________________________________________________________
        # ####THIS CAN BE WEAR THE REVIEW OF POTENTIALLY INCORRECT CLASSIFICATIONS CAN BE CHANGED####
        #
        # pd.set_option('display.max_columns', None)#this means all coulms of df will be printed
        #
        # data_df_2.rename(columns={'day': 'Day'}, inplace=True)
        # data_df_2.rename(columns={'monitor_name': 'FM'}, inplace=True)
        #
        # combined_df = pd.merge(data_df_2, join_df, on=['FM', 'Day'])
        #
        # class_refine =  1
        # if class_refine == 1 :
        #
            # #----------------------------------------
            # H_df = combined_df.loc[(combined_df['zero_velocity'] >= 600) & (combined_df['Predicted_rf'] == 'R')]
            #
            # G_df = combined_df.loc[(combined_df['zero_velocity'] >= 600) & (combined_df['zero_depth'] <= 10) & (combined_df['Predicted_rf'] == 'L') & (combined_df['ave_depth'] <= 20) & (combined_df['max_depth'] <= 20)]
            #
            # L_df = combined_df.loc[(combined_df['max_depth'] <= 100) & (combined_df['min_depth'] <= 100) & (combined_df['ave_depth'] <= 100)& (combined_df['Predicted_rf'] == 'H')]
            #
            # #----------------------------------------
            # for r in range(len(join_df)):
            #
            # row_FM = join_df.iloc[r,join_df.columns.get_loc('FM')]
            # row_Day = join_df.iloc[r,join_df.columns.get_loc('Day')]
            #
            # #-------------------------------------------------------------------------------------------------------------------------------------------------
            # #This updates Standing Water that has be classed as ragging
            #
            # if len(H_df.loc[(H_df.FM == row_FM) & (H_df.Day == row_Day)])== 1:
            #
            # join_df.iloc[r, join_df.columns.get_loc('Predicted_rf')] = 'H'
            # join_df.iloc[r, join_df.columns.get_loc('R')] = 0.999
            #
            # #-------------------------------------------------------------------------------------------------------------------------------------------------
            # #This updates Dry Pipes that have be classed as low flow
            #
            # if len(G_df.loc[(G_df.FM == row_FM) & (G_df.Day == row_Day)])== 1:
            #
            # join_df.iloc[r, join_df.columns.get_loc('Predicted_rf')] = 'G'
            # join_df.iloc[r, join_df.columns.get_loc('L')] = 0.999
            #
            # #-------------------------------------------------------------------------------------------------------------------------------------------------
            # #This updates Low Flows that have been classed as standing water
            #
            # if len(L_df.loc[(L_df.FM == row_FM) & (L_df.Day == row_Day)])== 1:
            #
            # join_df.iloc[r, join_df.columns.get_loc('Predicted_rf')] = 'L'
            # join_df.iloc[r, join_df.columns.get_loc('H')] = 0.999
            #
            # #-------------------------------------------------------------------------------------------------------------------------------------------------
        # #_____________________________________________________________________________________________________________________________________________
        # #This is the intial import of the dataframe and setup of the data worksheet
        #
        # #import datetime
        #
        # # wb_location = output_path+ '.xlsx'
        # wb_location = output_path
        # #________________________________________________________
        # #This combines the list of moniotrs with & without data
        # monitor_names_1D = join_df["FM"].unique()
        #
        # monitor_names = []
        #
        # for u in range(len(monitor_names_1D)):
        #
            # monitor_names.append(monitor_names_1D[u])
            #
        # monitor_names =  monitor_names + no_data_list
        #
        # #________________________________________________________
        #
        # days = join_df["Day"].unique()
        #
        # monitor_names.sort()
        #
        # sorted_days = sorted(days, key=lambda x: datetime.strptime(x, "%d/%m/%Y"))
        #
        # writer = ExcelWriter(wb_location)
        #
        # join_df.to_excel(writer,'Data', startcol=2,startrow=0, index = False)
        #
        # workbook= writer.book
        #
        # worksheet = writer.sheets['Data']
        #
        # header = workbook.add_format({'bold': True, 'border': 1})
        #
        # worksheet.write('A1', 'KEY', header)
        # worksheet.write('B1', 'MAX', header)
        #
        # worksheet.set_column(0, 0, 17.82)
        # worksheet.set_column(1, 4, 10.55)
        #
        # for r in range(1,len(join_df)+1):
        #
            # worksheet.write_formula(xl_rowcol_to_cell(r, 0), '='+xl_rowcol_to_cell(r, 2)+'&'+chr(34)+'_'+chr(34)+'&'+xl_rowcol_to_cell(r, 3))
            #
            # worksheet.write_formula(xl_rowcol_to_cell(r, 1), '=MAX('+xl_rowcol_to_cell(r, 5)+':'+xl_rowcol_to_cell(r, 22)+')')
        # #_____________________________________________________
        # #This is the setup of the output worksheet
        #
        # L_class_conditonal_format = workbook.add_format()
        # L_class_conditonal_format.set_bg_color('#b0f442')
        #
        # X_class_conditonal_format = workbook.add_format()
        # X_class_conditonal_format.set_bg_color('#f44141')
        #
        # Q_class_conditonal_format = workbook.add_format()
        # Q_class_conditonal_format.set_bg_color('#354d89')
        #
        # E_class_conditonal_format = workbook.add_format()
        # E_class_conditonal_format.set_bg_color('#897b34')
        #
        # R_class_conditonal_format = workbook.add_format()
        # R_class_conditonal_format.set_bg_color('#347bc1')
        #
        # B_class_conditonal_format = workbook.add_format()
        # B_class_conditonal_format.set_bg_color('#c10f50')
        #
        # H_class_conditonal_format = workbook.add_format()
        # H_class_conditonal_format.set_bg_color('#f2ebbc')
        #
        # D_class_conditonal_format = workbook.add_format()
        # D_class_conditonal_format.set_bg_color('#5aace2')
        #
        # V_class_conditonal_format = workbook.add_format()
        # V_class_conditonal_format.set_bg_color('#fff82d')
        #
        # P_class_conditonal_format = workbook.add_format()
        # P_class_conditonal_format.set_bg_color('#adede7')
        #
        # S_class_conditonal_format = workbook.add_format()
        # S_class_conditonal_format.set_bg_color('#f2c68c')
        #
        # G_class_conditonal_format = workbook.add_format()
        # G_class_conditonal_format.set_bg_color('#fff82d')
        #
        # y_col_format = workbook.add_format({'bold': True, 'border': 1})
        # x_col_format = workbook.add_format({'bold': True, 'border': 1})
        # x_col_format.set_rotation(90)
        #
        # event_x_col_format = workbook.add_format({'bold': True, 'border': 1})
        # event_x_col_format.set_rotation(90)
        # event_x_col_format.set_bg_color('#FFEE58')
        #
        # worksheet = workbook.add_worksheet(name='Output')
        # worksheet.conditional_format(xl_rowcol_to_cell(5, 1)+':'+xl_rowcol_to_cell(len(monitor_names)+4, len(sorted_days)), {'type':'text','criteria': 'containing','value':'L','format':L_class_conditonal_format})
        # worksheet.conditional_format(xl_rowcol_to_cell(5, 1)+':'+xl_rowcol_to_cell(len(monitor_names)+4, len(sorted_days)), {'type':'text','criteria': 'containing','value':'X','format':X_class_conditonal_format})
        # worksheet.conditional_format(xl_rowcol_to_cell(5, 1)+':'+xl_rowcol_to_cell(len(monitor_names)+4, len(sorted_days)), {'type':'text','criteria': 'containing','value':'Q','format':Q_class_conditonal_format})
        # worksheet.conditional_format(xl_rowcol_to_cell(5, 1)+':'+xl_rowcol_to_cell(len(monitor_names)+4, len(sorted_days)), {'type':'text','criteria': 'containing','value':'E','format':E_class_conditonal_format})
        # worksheet.conditional_format(xl_rowcol_to_cell(5, 1)+':'+xl_rowcol_to_cell(len(monitor_names)+4, len(sorted_days)), {'type':'text','criteria': 'containing','value':'R','format':R_class_conditonal_format})
        # worksheet.conditional_format(xl_rowcol_to_cell(5, 1)+':'+xl_rowcol_to_cell(len(monitor_names)+4, len(sorted_days)), {'type':'text','criteria': 'containing','value':'B','format':B_class_conditonal_format})
        # worksheet.conditional_format(xl_rowcol_to_cell(5, 1)+':'+xl_rowcol_to_cell(len(monitor_names)+4, len(sorted_days)), {'type':'text','criteria': 'containing','value':'H','format':H_class_conditonal_format})
        # worksheet.conditional_format(xl_rowcol_to_cell(5, 1)+':'+xl_rowcol_to_cell(len(monitor_names)+4, len(sorted_days)), {'type':'text','criteria': 'containing','value':'D','format':D_class_conditonal_format})
        # worksheet.conditional_format(xl_rowcol_to_cell(5, 1)+':'+xl_rowcol_to_cell(len(monitor_names)+4, len(sorted_days)), {'type':'text','criteria': 'containing','value':'V','format':V_class_conditonal_format})
        # worksheet.conditional_format(xl_rowcol_to_cell(5, 1)+':'+xl_rowcol_to_cell(len(monitor_names)+4, len(sorted_days)), {'type':'text','criteria': 'containing','value':'P','format':P_class_conditonal_format})
        # worksheet.conditional_format(xl_rowcol_to_cell(5, 1)+':'+xl_rowcol_to_cell(len(monitor_names)+4, len(sorted_days)), {'type':'text','criteria': 'containing','value':'S','format':S_class_conditonal_format})
        #
        # worksheet.conditional_format(xl_rowcol_to_cell(5, 1)+':'+xl_rowcol_to_cell(len(monitor_names)+4, len(sorted_days)), {'type':'text','criteria': 'containing','value':'G','format':G_class_conditonal_format})
        #
        # for r in range(len(monitor_names)):
        #
            # worksheet.write(xl_rowcol_to_cell(r+5, 0), monitor_names[r], y_col_format)
            #
            # for c in range(len(sorted_days)):
            #
            # worksheet.write_formula(xl_rowcol_to_cell(r+5, c+1),
            # 'IFERROR(VLOOKUP('+xl_rowcol_to_cell(r+5, 0)+'&'+chr(34) + '_' + chr(34)+ '&' +  xl_rowcol_to_cell(4, c+1)+',Data!$A:$E,5,FALSE),'+chr(34)+'-'+chr(34)+')')
            #
        # #-------------------------------------------------------------------------------------------------------------------
        # # This allows for alist to be created of the events in the dialogue box
        #
        # #if self.event_analysis.get() == 1:
        # if self.chkCompleteEventsAnalysis.isChecked():
        #
            # event_day_list = []
            #
            # tree_entries=self.tree.get_children()
            #
            # print('LENGTH tree_entries = ' + str(len(tree_entries)))
            #
            # number_of_subplots = len(tree_entries)
            #
            # v = 0
            #
            # pie_colours = []
            #
            #
            # for each in tree_entries:
            #
            # event_name =  self.tree.item(each)['text']
            #
            # if event_name [:2] != 'X_':
            #
            # dateformat = '%d/%m/%Y %H:%M:%S'
            #
            # event_start_1 = datetime.datetime.strptime(self.tree.item(each)['values'][0], dateformat)
            # event_end_1 = datetime.datetime.strptime(self.tree.item(each)['values'][1], dateformat)
            #
            # start_truncated = datetime.date(event_start_1.year, event_start_1.month, event_start_1.day)
            # end_truncated = datetime.date(event_end_1.year, event_end_1.month, event_end_1.day)
            #
            # p = int(((end_truncated- start_truncated).total_seconds() / 86400)+1)
            #
            # event_day_range = pd.date_range(start = start_truncated, periods = p, freq='D').tolist()
            #
            # event_name =  self.tree.item(each)['text']
            #
            # event_day_list +=  event_day_range
            #
            # #____________________________________________________________________________________________________________________________
            # #This is the section that calcualtes the number of diffrent classifications during each event and create pie
            #
            # DAY_List = [d.strftime("%d/%m/%Y") for d in event_day_range]
            #
            # event_analysis_df = join_df[join_df['Day'].isin(DAY_List)]
            #
            # event_analysis_df_2 = event_analysis_df.groupby('Predicted_rf').count()
            #
            # labels = event_analysis_df_2.index.tolist()
            #
            # #___________________________________________________
            # #This creates a list of colours, so the same are applyed for each pie
            #
            # for c in range(len(labels)):
            #
            # if labels[c] == 'W':
            # pie_colours.append('white')
            # elif labels[c] == 'B':
            # pie_colours.append('#c10f50')
            # elif labels[c] == 'D':
            # pie_colours.append('#5aace2')
            # elif labels[c] == 'E':
            # pie_colours.append('#897b34')
            # elif labels[c] == 'H':
            # pie_colours.append('#f2ebbc')
            # elif labels[c] == 'L':
            # pie_colours.append('#b0f442')
            # elif labels[c] == 'P':
            # pie_colours.append('#adede7')
            # elif labels[c] == 'Q':
            # pie_colours.append('#354d89')
            # elif labels[c] == 'R':
            # pie_colours.append('#347bc1')
            # elif labels[c] == 'S':
            # pie_colours.append('#f2c68c')
            # elif labels[c] == 'V':
            # pie_colours.append('#fff82d')
            # elif labels[c] == 'X':
            # pie_colours.append('#f44141')
            # elif labels[c] == 'G':
            # pie_colours.append('#fff82d')
            #
            # #___________________________________________________
            # #This updates the labels with the full name intead of single letter
            #
            # for n, i in enumerate(labels):
            # if i == 'W':
            # labels[n] = 'Working'
            # if i == 'B':
            # labels[n] = 'Backing Up'
            # if i == 'D':
            # labels[n] = 'Depth Problem'
            # if i == 'E':
            # labels[n] = 'Surcharge'
            # if i == 'H':
            # labels[n] = 'Standing Water'
            # if i == 'L':
            # labels[n] = 'Low Depth'
            # if i == 'P':
            # labels[n] = 'Pluming'
            # if i == 'Q':
            # labels[n] = 'Low Flow'
            # if i == 'R':
            # labels[n] = 'Ragging'
            # if i == 'S':
            # labels[n] = 'Sediment'
            # if i == 'V':
            # labels[n] = 'Velocity Problem'
            # if i == 'X':
            # labels[n] = 'Not Working'
            # if i == 'G':
            # labels[n] = 'Dry Pipe'
            #
            # sizes = event_analysis_df_2['X'].tolist()
            #
            # #---------------------------------
            # #1st subplot
            # if v == 0:
            #
            # pie_fig = plt.figure()
            # ax = pie_fig.add_subplot(111)
            # ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, radius = 0.8, colors= pie_colours,
            # wedgeprops=dict(edgecolor='#2471A3'), textprops={'fontsize': 8},labeldistance=1,rotatelabels = True)
            # ax.set_title(event_name,color = 'steelblue')
            # ax.axis('equal')
            #
            # #---------------------------------
            # # Remaining subplots
            # else:
            #
            # n = len(pie_fig.axes)
            # for i in range(n):
            # pie_fig.axes[i].change_geometry(n+1, 1, i+1)
            #
            # ax = pie_fig.add_subplot(n+1, 1, n+1)
            # ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, radius = 0.8, colors= pie_colours,
            # wedgeprops=dict(edgecolor= '#2471A3'), textprops={'fontsize': 8}, labeldistance=1,rotatelabels = True)
            # ax.set_title(event_name,color = 'steelblue')
            # ax.axis('equal')
            # #____________________________________________________________________________________________________________________________
            # event_day_range.clear()
            # DAY_List.clear()
            # pie_colours.clear()
            #
            # #event_day_list.clear()
            #
            # del event_analysis_df
            # del event_analysis_df_2
            # v += 1
            #
            # pie_fig.suptitle('Event Monitor Data Classifications', fontsize=16, color = 'steelblue')
            # pie_fig.set_size_inches(5, 8, forward=True)
            # pie_fig.canvas.set_window_title('Event Analysis')
            #
            #
            # RG_props = dict(boxstyle='round', facecolor='teal', alpha=0.5)
            #
            # flow_stats_box = plt.text(0, -0.1, monitor_names, transform=ax.transAxes, fontsize=8,
            # verticalalignment='top', bbox=RG_props, wrap = True)
            #
            # #-----------------------------------------------------------------
            # #This updates the formating of the header to show the event dates
            #
            # event_day_list = [d.strftime("%d/%m/%Y") for d in event_day_list]
            #
            # worksheet.set_column(1, len(sorted_days), 2.73)
            # for c in range(len(sorted_days)):
            #
            # if sorted_days[c] in event_day_list:
            #
            # worksheet.write(xl_rowcol_to_cell(4, c+1), sorted_days[c], event_x_col_format)
            #
            # else:
            #
            # worksheet.write(xl_rowcol_to_cell(4, c+1), sorted_days[c], x_col_format)
            #
        # #-----------------
        # else:
        #
            # worksheet.set_column(1, len(sorted_days)+67, 2.73)
            #
            # for c in range(len(sorted_days)):
            #
            # worksheet.write(xl_rowcol_to_cell(4, c+1), sorted_days[c], x_col_format)
            #
        # #-------------------------------------------------------------------------------------------------------------------
        # key_text = workbook.add_format({'bold': True,})
        #
        # worksheet.write(xl_rowcol_to_cell(1, 2), 'B', B_class_conditonal_format)
        # worksheet.write(xl_rowcol_to_cell(1, 3), 'Backing Up', key_text)
        #
        # worksheet.write(xl_rowcol_to_cell(1, 8), 'D', D_class_conditonal_format)
        # worksheet.write(xl_rowcol_to_cell(1, 9), 'Depth Problem', key_text)
        #
        # worksheet.write(xl_rowcol_to_cell(1, 14), 'E', E_class_conditonal_format)
        # worksheet.write(xl_rowcol_to_cell(1, 15), 'Surcharge', key_text)
        #
        # worksheet.write(xl_rowcol_to_cell(1, 19), 'H', H_class_conditonal_format)
        # worksheet.write(xl_rowcol_to_cell(1, 20), 'Standing Water', key_text)
        #
        # worksheet.write(xl_rowcol_to_cell(1, 25), 'L', L_class_conditonal_format)
        # worksheet.write(xl_rowcol_to_cell(1, 26), 'Low Depth', key_text)
        #
        # worksheet.write(xl_rowcol_to_cell(1, 30), 'P', P_class_conditonal_format)
        # worksheet.write(xl_rowcol_to_cell(1, 31), 'Pluming', key_text)
        #
        # worksheet.write(xl_rowcol_to_cell(1, 35), 'Q', Q_class_conditonal_format)
        # worksheet.write(xl_rowcol_to_cell(1, 36), 'Low Flow', key_text)
        #
        # worksheet.write(xl_rowcol_to_cell(1, 40), 'R', R_class_conditonal_format)
        # worksheet.write(xl_rowcol_to_cell(1, 41), 'Ragging', key_text)
        #
        # worksheet.write(xl_rowcol_to_cell(1, 45), 'S', S_class_conditonal_format)
        # worksheet.write(xl_rowcol_to_cell(1, 46), 'Sediment', key_text)
        #
        # worksheet.write(xl_rowcol_to_cell(1, 50), 'V', V_class_conditonal_format)
        # worksheet.write(xl_rowcol_to_cell(1, 51), 'Velocity Problem', key_text)
        #
        # worksheet.write(xl_rowcol_to_cell(1, 56), 'W')
        # worksheet.write(xl_rowcol_to_cell(1, 57), 'Working', key_text)
        #
        # worksheet.write(xl_rowcol_to_cell(1, 61), 'G', G_class_conditonal_format)
        # worksheet.write(xl_rowcol_to_cell(1, 62), 'Dry Pipe', key_text)
        #
        # worksheet.write(xl_rowcol_to_cell(1, 66), 'X', X_class_conditonal_format)
        # worksheet.write(xl_rowcol_to_cell(1, 67), 'Not Working', key_text)
        #
        # #_____________________________________________________
        # #This is the setup of the Confidence worksheet
        #
        # worksheet = workbook.add_worksheet(name='Confidence')
        #
        # two_decimal_place = workbook.add_format()
        # two_decimal_place.set_num_format('0.00')
        #
        # worksheet.set_column(1, len(sorted_days), 4.45)
        #
        # for r in range(len(monitor_names)):
        #
            # worksheet.write(xl_rowcol_to_cell(r+1, 0), monitor_names[r], y_col_format)
            #
            # for c in range(len(sorted_days)):
            #
            # worksheet.write_formula(xl_rowcol_to_cell(r+1, c+1),
            # 'IFERROR(VLOOKUP('+xl_rowcol_to_cell(r+1, 0)+'&'+chr(34) + '_' + chr(34)+ '&' +  xl_rowcol_to_cell(0, c+1)+',Data!$A:$B,2,FALSE),'+chr(34)+'-'+chr(34)+')',two_decimal_place )
            #
        # for c in range(len(sorted_days)):
        #
            # worksheet.write(xl_rowcol_to_cell(0, c+1), sorted_days[c], x_col_format)
            #
        # worksheet.conditional_format(xl_rowcol_to_cell(1, 1)+':'+xl_rowcol_to_cell(len(monitor_names), len(sorted_days)), {'type':'3_color_scale',})
        #
        #
        # writer.save()
        # writer.close()
        #
        # time.sleep(1)
        #
        # # self.pval = 0
        # # self.progressbar['value'] = self.pval
        # # self.progressbar.update_idletasks()
        #
# # \        print('Classification Complete')
#
        # class_end_time = datetime.now()
        #
        # # print('Started = ' + str(class_start_time) + ' - Finished = ' + str(class_end_time))
        # #
        # # ctypes.windll.user32.MessageBoxW(0, "Classification Complete", "Machine Learning", 0)
        # #
        # # if self.event_analysis.get() == 1:
            # # pie_fig.show()
            # #

    # def data_class():
    #
        # # self.date_check_class = tk.IntVar()
        # # self.events_class = tk.IntVar()
        # # self.event_analysis = tk.IntVar()
        # #
        # # win_height = 800#580
        # # win_width = 510
        # #
        # # self.class_win = tk.Toplevel()
        # # self.class_win.wm_title("Machine Learning Data Classification")
        # #
        # # FM_frame = tk.Frame(self.class_win)
        # # FM_frame.grid(row=0, column=0, pady=5, sticky = 'ns', rowspan = 4)
        # #
        # # self.FM_label = ttk.Label(FM_frame, text = "Flow Monitors")
        # # self.FM_label.grid(row=0, column=0, padx=(12,0),pady=(5,0), columnspan = 3, sticky = 's')
        # #
        # # self.data_class_multi_FM_yScroll = tk.Scrollbar(FM_frame, orient=tk.VERTICAL)
        # # self.data_class_multi_FM_yScroll.grid(row=1, column=0, pady=5, sticky = 'ns', rowspan = 4)
        # #
        # # self.data_class_FM_multi_List_Box =tk.Listbox(FM_frame, yscrollcommand=self.data_class_multi_FM_yScroll.set, selectmode='extended',height = 35)
        # # self.data_class_FM_multi_List_Box.config(highlightbackground='#71004B', highlightthickness = 2, exportselection=False)
        # # self.data_class_FM_multi_List_Box.grid(row=1,column=1,padx=5, pady=(1,5), sticky = 'ns', rowspan = 4)
        # # self.data_class_multi_FM_yScroll['command'] = self.data_class_FM_multi_List_Box.yview
        # #
        # # DM_frame = tk.Frame(self.class_win)
        # # DM_frame.grid(row=0, column=1, pady=5, sticky = 'ns', rowspan = 4)
        # #
        # # self.DM_label = ttk.Label(DM_frame, text = "Depth Monitors")
        # # self.DM_label.grid(row=0, column=0, padx=(12,0),pady=(5,0), columnspan = 3, sticky = 's')
        # #
        # # self.data_class_multi_DM_yScroll = tk.Scrollbar(DM_frame, orient=tk.VERTICAL)
        # # self.data_class_multi_DM_yScroll.grid(row=1, column=0, pady=5, sticky = 'ns', rowspan = 4)
        # #
        # # self.data_class_DM_multi_List_Box =tk.Listbox(DM_frame, yscrollcommand=self.data_class_multi_DM_yScroll.set, selectmode='extended',height = 35)
        # # self.data_class_DM_multi_List_Box.config(highlightbackground='#71004B', highlightthickness = 2, exportselection=False)
        # # self.data_class_DM_multi_List_Box.grid(row=1,column=1,padx=5, pady=(1,5), sticky = 'ns', rowspan = 4)
        # # self.data_class_multi_DM_yScroll['command'] = self.data_class_DM_multi_List_Box.yview
        # #
        # # value_input_frame = tk.Frame(self.class_win,highlightbackground='#71004B', highlightthickness = 2)
        # # value_input_frame.grid(row=0, column=2, padx=5, pady=(10,5), sticky = 'ns')
        # #
        # # file_select_frame = tk.Frame(self.class_win,highlightbackground='#71004B', highlightthickness = 2)
        # # file_select_frame.grid(row=1, column=2, padx=5, pady=5, sticky = 'ns')
        # #
        # # dates_frame = tk.Frame(self.class_win,highlightbackground='#71004B', highlightthickness = 2)
        # # dates_frame.grid(row=2, column=2, padx=5, pady=5, sticky = 'ns')
# # #_____________________
        # # self.param_label = ttk.Label(value_input_frame, text = "Algorithm Parameters:")
        # # self.param_label.grid(row=0, column=0, padx=(5,0),pady=(5,5), columnspan = 2, sticky = 'w')
        # #
        # # self.n_estimators_label = ttk.Label(value_input_frame, text = "n_estimators:")#
        # # self.n_estimators_label.grid(row=1, column=0, padx=(17,0),pady=(10,10))#
        # #
        # # self.n_estimators_entry = ttk.Entry(value_input_frame)
        # # self.n_estimators_entry.grid(row=1, column=1, padx=(5,12), pady=(10,10))
        # # self.n_estimators_entry.insert(1, 200)
        # #
        # # self.max_depth_label = ttk.Label(value_input_frame, text = "max_depth:")
        # # self.max_depth_label.grid(row=1, column=2, padx=5, pady=(10,10))
        # #
        # # self.max_depth_entry = ttk.Entry(value_input_frame)
        # # self.max_depth_entry.grid(row=1, column=3, padx=(0,5), pady=(10,10))
        # # self.max_depth_entry.insert(0, 110)
# # #_____________________
        # # self.max_features_label = ttk.Label(value_input_frame, text = "max_features:")#
        # # self.max_features_label.grid(row=2, column=0, padx=(17,0),pady=(10,10))#
        # #
        # # self.max_features_entry = ttk.Entry(value_input_frame)
        # # self.max_features_entry.grid(row=2, column=1, padx=(5,12), pady=10)
        # # self.max_features_entry.insert(0, 'auto')
        # #
        # # self.min_samples_leaf_label = ttk.Label(value_input_frame, text = "min_samples_leaf:")
        # # self.min_samples_leaf_label.grid(row=2, column=2, padx=5, pady=10)
        # #
        # # self.min_samples_leaf_entry = ttk.Entry(value_input_frame)
        # # self.min_samples_leaf_entry.grid(row=2, column=3, padx=(0,5), pady=10)
        # # self.min_samples_leaf_entry.insert(0, 4)
# # #_____________________
        # # self.bootstrap_label = ttk.Label(value_input_frame, text = "bootstrap:")#
        # # self.bootstrap_label.grid(row=3, column=0, padx=(17,0), pady=(10,10))#
        # #
        # # self.bootstrap_entry = ttk.Combobox(value_input_frame, values = [True, False])
        # # self.bootstrap_entry.grid(row=3, column=1, padx=(5,12), pady=10)
        # # self.bootstrap_entry.insert(0, 'True')
        # #
        # # self.min_samples_split_label = ttk.Label(value_input_frame, text = "min_samples_split:")
        # # self.min_samples_split_label.grid(row=3, column=2, padx=5, pady=10)
        # #
        # # self.min_samples_split_entry = ttk.Entry(value_input_frame)
        # # self.min_samples_split_entry.grid(row=3, column=3, padx=(0,5), pady=10)
        # # self.min_samples_split_entry.insert(0, 5)
# # #_____________________
        # # self.training_fp_label = ttk.Label(file_select_frame, text = "Training Data File Path:")
        # # self.training_fp_label.grid(row=2, column=0, padx=5, pady=(10,1), sticky = 'w')
        # #
        # # self.training_fp_entry = ttk.Entry(file_select_frame, width = 66)
        # # self.training_fp_entry.grid(row=3, column=0, padx=5, pady=(5,20), sticky = 'w', columnspan = 5)
        # # #self.training_fp_entry.insert(0,'C:/Users/daniel.bourne/AppData/Local/Programs/Python/Python36-32/training_data_3.csv')
        #
        # # self.training_fp_btn = ttk.Button(file_select_frame, text="", command = lambda:training_data_fp())
        # # self.training_fp_btn.grid(row=3, column=6, padx=5, pady=(5,20), sticky = 'w')
        # #
        # # self.output_fp_label = ttk.Label(file_select_frame, text = "Output File Path:")
        # # self.output_fp_label.grid(row=4, column=0, padx=5, pady=(20,1), sticky = 'w')
        # #
        # # self.output_fp_entry = ttk.Entry(file_select_frame,  width = 66)
        # # self.output_fp_entry.grid(row=5, column=0, padx=5, pady=(5,20), sticky = 'w', columnspan = 5)
        # # #self.output_fp_entry.insert(0,'C:/Users/daniel.bourne/Desktop/out')
        # #
        # # self.output_fp_btn = ttk.Button(file_select_frame, text="", command = lambda:class_output_fp())
        # # self.output_fp_btn.grid(row=5, column=6, padx=5, pady=(5,20), sticky = 'w')
        # # #_____________________
        # # self.fp_checkbox = tk.Checkbutton(dates_frame, text='FP', command = lambda:class_date_toggle(), variable = self.date_check_class)
        # # self.fp_checkbox.grid(row=0, column=0, pady=(10,5), padx = 10)
        # # self.fp_checkbox.select()
        # #
        # # self.cal_btn = ttk.Button(dates_frame, text="Calendar Input", command = lambda:cal_input_dates())
        # # self.cal_btn.grid(row=0, column=1)
        # # self.cal_btn.configure(state="disabled")
        #
        # #_________________________________________________________
        # # def cal_input_dates():
        # #
            # # def set_start(event):
            # # print(start_cal.get_date())
            # # self.start_date_entry.delete(0, 'end')
            # # self.start_date_entry.insert(0, start_cal.get_date())
            # #
            # # def set_end(event):
            # # print(end_cal.get_date())
            # # self.end_date_entry.delete(0, 'end')
            # # self.end_date_entry.insert(0, end_cal.get_date())
            # #
            # # def date_lost_focus(event):
            # # print('FOCUS LOST!')
            # # #self.class_win.destroy()
            # #
            # # self.class_win = tk.Toplevel()
            # # self.class_win.wm_title("Calender")
            # # self.class_win.bind("<FocusOut>", date_lost_focus)
            # # self.class_win.focus_set()
            # #
            # # self.start_cal_label = ttk.Label(self.class_win, text = "Start Date:")
            # # self.start_cal_label.grid(row=0, column=0,sticky = 'w')
            # #
            # # start_cal = Calendar(self.class_win, font="Arial 14", selectmode='day', locale='en_UK',background = '#71004B', headersbackground = '#71004B', bordercolor = 'black')
            # # start_cal.grid(row=1, column=0)
            # # start_cal.bind("<<CalendarSelected>>", set_start)
            # #
            # #
            # # self.end_cal_label = ttk.Label(self.class_win, text = "End Date:")
            # # self.end_cal_label.grid(row=0, column=1, sticky = 'w')
            # #
            # # end_cal = Calendar(self.class_win, font="Arial 14", selectmode='day', locale='en_UK',background = '#71004B', headersbackground = '#71004B', bordercolor = 'black')
            # # end_cal.grid(row=1, column=1)
            # # end_cal.bind("<<CalendarSelected>>", set_end)
            # #
            # # #_______________________________________________________
            # # w = 742
            # # h = 262
            # #
            # # ws = self.class_win.winfo_screenwidth()
            # # hs = self.class_win.winfo_screenheight()
            # #
            # # x = (ws/1.5) - (w/1.5)
            # # y = (hs/2) - (h/2)
            # #
            # # self.class_win.geometry('%dx%d+%d+%d' % (w, h, x, y))
        # # #_________________________________________________________
        #
        # # self.start_date_label = ttk.Label(dates_frame, text = "Start Date:")
        # # self.start_date_label.grid(row=1, column=0, padx=5, pady=(10,20), sticky = 'w')
        # #
        # # self.start_date_entry = ttk.Entry(dates_frame, width = 25, justify='center')
        # # self.start_date_entry.grid(row=1, column=1, padx=(5,23), pady=(10,20), sticky = 'w')
        # # self.start_date_entry.insert(0, 'dd/mm/yyyy')
        # # self.start_date_entry.configure(state="disabled")
        # #
        # # self.end_date_label = ttk.Label(dates_frame, text = "End Date:")
        # # self.end_date_label.grid(row=1, column=3, padx=(23,5), pady=(10,20), sticky = 'w')
        # #
        # # self.end_date_entry = ttk.Entry(dates_frame, width = 25, justify='center')
        # # self.end_date_entry.grid(row=1, column=4, padx=5, pady=(10,20), sticky = 'w')
        # # self.end_date_entry.insert(0, 'dd/mm/yyyy')
        # # self.end_date_entry.configure(state="disabled")
        # #
        # # self.events_checkbox = tk.Checkbutton(dates_frame, text='Load Monitor Failure Events?', command = lambda:load_events_class(), variable = self.events_class)#
        # # self.events_checkbox.grid(row=2, column=0, pady=(10,5), padx = 5, columnspan = 3, sticky = 'w')
        # #
        # # self.analysis_events_checkbox = tk.Checkbutton(dates_frame, text='Complete Events Analysis?', command = lambda:load_events_analysis_class(), variable = self.event_analysis)#
        # # self.analysis_events_checkbox.grid(row=2, column=2, pady=(10,5), padx = 5, columnspan = 3, sticky = 'w')
        # #
        # # self.progressbar=ttk.Progressbar(self.class_win,orient='horizontal',length=300,mode='indeterminate')
        # # self.progressbar.grid(row=3, column=2)
# #_____________________________________________________________________________________________________________________________________________________
        #
        # self.data_class_button = ttk.Button(self.class_win, text = "Run",  command = lambda:flow_survey_data_classification())
        # self.data_class_button.grid(row=4, column=2)
        #
        # z= 0
        # for i in range(len(FlowServ.FM_file_name_list)):
        #
            # self.data_class_FM_multi_List_Box.insert(z, FlowServ.FM_file_name_list[i])
            # self.data_class_DM_multi_List_Box.insert(z, FlowServ.FM_file_name_list[i])
            #
            # z=+1
        # #_________________________________
        # w = 821
        # h = 635
        #
        # ws = self.class_win.winfo_screenwidth()
        # hs = self.class_win.winfo_screenheight()
        #
        # x = (ws/2) - (w/2)
        # y = (hs/2) - (h/2)
        #
        # self.class_win.geometry('%dx%d+%d+%d' % (w, h, x, y))
        # self.class_win.resizable(False, False)
        #
    # def cal_input_dates():
    #
        # self.class_win = tk.Toplevel()
        # self.class_win.wm_title("Calender")
        # self.class_win.bind("<FocusOut>", date_lost_focus)
        # self.class_win.focus_set()
        #
        # self.start_cal_label = ttk.Label(self.class_win, text = "Start Date:")
        # self.start_cal_label.grid(row=0, column=0,sticky = 'w')
        #
        # start_cal = Calendar(self.class_win, font="Arial 14", selectmode='day', locale='en_UK',background = '#71004B', headersbackground = '#71004B', bordercolor = 'black')
        # start_cal.grid(row=1, column=0)
        # start_cal.bind("<<CalendarSelected>>", set_start)
        #
        #
        # self.end_cal_label = ttk.Label(self.class_win, text = "End Date:")
        # self.end_cal_label.grid(row=0, column=1, sticky = 'w')
        #
        # end_cal = Calendar(self.class_win, font="Arial 14", selectmode='day', locale='en_UK',background = '#71004B', headersbackground = '#71004B', bordercolor = 'black')
        # end_cal.grid(row=1, column=1)
        # end_cal.bind("<<CalendarSelected>>", set_end)
        #
        # #_______________________________________________________
        # w = 742
        # h = 262
        #
        # ws = self.class_win.winfo_screenwidth()
        # hs = self.class_win.winfo_screenheight()
        #
        # x = (ws/1.5) - (w/1.5)
        # y = (hs/2) - (h/2)
        #
        # self.class_win.geometry('%dx%d+%d+%d' % (w, h, x, y))
        #
    # def set_start(event):
        # print(start_cal.get_date())
        # self.start_date_entry.delete(0, 'end')
        # self.start_date_entry.insert(0, start_cal.get_date())
        #
    # def set_end(event):
        # print(end_cal.get_date())
        # self.end_date_entry.delete(0, 'end')
        # self.end_date_entry.insert(0, end_cal.get_date())
        #
    # def date_lost_focus(event):
        # print('FOCUS LOST!')
        # #self.class_win.destroy()
