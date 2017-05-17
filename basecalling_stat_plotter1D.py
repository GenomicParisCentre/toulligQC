import pandas as pd
import seaborn as sns
import numpy as np
import matplotlib
matplotlib.use('Agg')
from matplotlib import cm
import matplotlib.pyplot as plt
import re
import getter1D
import os



class basecalling_stat_plotter1D:
    """
    Plots different graphs for exploitation of minion runs from Albacore file log
    """

    def __init__(self, path_sequencing_summary, pdf, run_name):
        self.sequencing_summary = pd.read_csv(path_sequencing_summary, sep="\t")
        self.channel = self.sequencing_summary['channel']
        self.sequencing_summary[self.sequencing_summary == 0] = np.nan
        self.selection = getter1D.get_barcode()
        self.selection_original = self.selection
        self.fast5_tot = len(self.sequencing_summary)
        self.pdf = pdf
        self.selection.sort()
        self.fastq_length_array = getter1D.get_fastq(self.selection, run_name)

    def meanqscore_barcode(self):
        dataframe_meanqscore_barcode = self.sequencing_summary[['mean_qscore_template','barcode_arrangement']]
        barcode_selection = dataframe_meanqscore_barcode[dataframe_meanqscore_barcode['barcode_arrangement'].isin(self.selection)]

        for barcode in self.selection:
            meanq_score = barcode_selection[barcode_selection['barcode_arrangement'] == barcode].mean()
            meanq_score = meanq_score.tolist()[0]
            completeName = os.path.join('statistics/', barcode)
            file = open(completeName,'a')
            file.write("mean.qscore.template={}\n".format(meanq_score))
            file.close()
            print('fini')


    def date(self):
        """
        Gets the date of Mimion run
        """
        filename = self.sequencing_summary['filename']
        for index, file in enumerate(filename):
            exp = self.sequencing_summary['filename'][index]
            break
        m = re.search(r'(_(\d+)_)', exp)
        return m.group(2)

    def stat_generation(self):
        """
        Generates a dictionary of statistics such as quartile, std for the creation of a log file like aozan from the summary log provided by Albacore
        """
        num_called_template = self.sequencing_summary['num_called_template']
        mean_qscore_template = self.sequencing_summary['mean_qscore_template']
        statistics_num_called_template = pd.DataFrame.describe(num_called_template).drop("count")
        statistics_mean_qscore_template = pd.DataFrame.describe(mean_qscore_template).drop("count")
        return statistics_num_called_template, statistics_mean_qscore_template

    def barcode_pie_chart(self):
        """
        Plots the barcode pie chart from the selection of barcodes
        """
        # Ne doit pas excéder 10

        for element in self.selection:


            if all(self.sequencing_summary['barcode_arrangement'] != element):
                print("The barcode {} doesn't exist".format(element))
                return False

        barcode = self.sequencing_summary['barcode_arrangement']
        count1 = barcode.value_counts()
        count = count1.sort_index()[self.selection]
        unclassified = sum(count1[~count1.index.isin(self.selection)])
        ##Watch out must be placed after the operation
        self.selection.append("unclassified")
        ##
        count['unclassified'] = unclassified
        total = sum(count1)

        cs = cm.Paired(np.arange(len(self.selection)) / len(self.selection))

        sizes = [(100 * chiffre) / total for chiffre in count.values]
        if len(self.selection) <= 10:
            fig1, ax1 = plt.subplots()
            ax1.pie(sizes, labels=self.selection, autopct='%1.1f%%', startangle=90, colors=cs)
            ax1.axis('equal')

        else:
            fig = plt.figure(figsize=(20, 10))
            ax1 = fig.add_subplot(111)
            length = np.arange(0, len(count))
            ax1.bar(length, count, color=cs)
            ax1.set_xticks(length)
            ax1.set_xticklabels(self.selection)

        plt.savefig('images/image5.png')
        self.pdf.savefig()
        plt.close()


    #Launch after barcode pie chart because of self.selection
    def reads_size_selection_barcode(self):
        """
        Plots the histogram of reads size by bins of 100
        """
        if self.fastq_length_array == []:
            print('There is a mistake')
            return False
        plt.hist(self.fastq_length_array, edgecolor="#E6E6E6", color="#EE6666", bins=range(min(self.fastq_length_array), max(self.fastq_length_array) + 100, 100))
        plt.xlabel("fastq size for barcode selection")
        plt.ylabel("Count")
        plt.xlim(0,6000)
        plt.title("reads size")
        plt.savefig('images/image7.png')
        self.pdf.savefig()
        plt.close()

    def counter(self):
        """
        Paricipates to the count df nucleotide(A,T,C,G)" \
        """
        return self.counter_template, self.total_nucs_template

    def statistics_read_size(self):
        """
        Gets statistics from the file containing the fastq bz2 files decompressed
        """
        series_read_size = pd.Series(self.fastq_length_array)
        statistics = pd.Series.describe(series_read_size)
        return statistics


    def histogram_count_reads(self):
        """
        Plots the histogram of count of different types of reads: template, complement, full_2D from albacore log file
        """

        # Count of fast5 total
        fast5tot = len(self.sequencing_summary)
        # Count of template reads
        template = len(self.sequencing_summary['num_called_template'].dropna())

         #Count of complement reads
        read_type = [fast5tot, template]
        label = ("fast5tot", "template")
        nd = np.arange(len(read_type))

        # Histogram of differents reads count(template, complement, fast2D)
        plt.bar(nd, read_type, align='center', color=["lightblue", "salmon"])
        plt.xticks(nd, label)
        plt.xlabel("read type")
        plt.ylabel("Counts")
        plt.title("Counts of read template")
        plt.savefig('images/image1.png')
        self.pdf.savefig()
        plt.close()

    def quality_reads_boxplot(self):
        """
        Plots a boxplot of reads quality
        """
        dataframe = self.sequencing_summary.loc[:, ["mean_qscore_template"]]
        sns.boxplot(data=dataframe)
        plt.title('Boxplot of read quality')
        plt.ylabel('Phred score')
        plt.savefig('images/image2.png')
        self.pdf.savefig()
        plt.close()



    def channel_count(self):
        """
        Plots an histogram of channel count
        """
        fig, ax = plt.subplots()
        ax.hist(self.sequencing_summary['channel'], edgecolor='black',  bins=range(min(self.sequencing_summary['channel']), max(self.sequencing_summary['channel']) + 64, 64))
        ax.set_xlabel("Channel number")
        ax.set_ylabel("Count")
        ax.set_title("Channel counts")
        plt.savefig('images/image3.png')
        self.pdf.savefig()
        plt.close()



    def read_time(self):
        """
        Plots an histogram of reads length
        """
        start_time = self.sequencing_summary["start_time"] / 3600
        time_sort = sorted(start_time)
        plt.scatter(time_sort, np.arange(len(time_sort)))
        plt.ylabel("produced reads")
        plt.xlabel("hour")
        plt.title("Read produced along the run")
        plt.savefig('images/image4.png')
        self.pdf.savefig()
        plt.close()

    def minion_flowcell_layout(self):
        """
        Represents the layout of a minion flowcell
        """
        seeds = [125, 121, 117, 113, 109, 105, 101, 97,
                 93, 89, 85, 81, 77, 73, 69, 65,
                 61, 57, 53, 49, 45, 41, 37, 33,
                 29, 25, 21, 17, 13, 9, 5, 1]

        flowcell_layout = []
        for s in seeds:
            for block in range(4):
                 for row in range(4):
                    flowcell_layout.append(s + 128 * block + row)
        return flowcell_layout

    def plot_performance(self, pore_measure):
        """
        Plots the pore performance in terms of reads per pore
        @:param pore_measure: reads number per pore
        """
        flowcell_layout = self.minion_flowcell_layout()

        pore_values = []
        for pore in flowcell_layout:
            if pore in pore_measure:
                pore_values.append(pore_measure[pore])
            else:
                pore_values.append(0)

        # make a data frame of the lists
        d = {'rownum': list(range(1, 17)) * 32,
             'colnum': sorted(list(range(1, 33)) * 16),
             'tot_reads': pore_values,
             'labels': flowcell_layout}

        df = pd.DataFrame(d)

        d = df.pivot("rownum", "colnum", "tot_reads")
        plt.figure(figsize=(20, 10))
        sns.heatmap(d, annot=True, fmt="d", linewidths=.5, cmap="YlGnBu")
        plt.title('Channel occupancy')
        plt.savefig('images/image6.png')
        self.pdf.savefig()
        plt.close()


    def occupancy_pore(self):
        channel_count = self.channel
        total_number_reads_per_pore = pd.value_counts(channel_count)
        Series = pd.DataFrame.describe(total_number_reads_per_pore)
        return pd.Series.to_dict(Series)

    def get_selection(self):
        return self.selection

    def statistics_dataframe(self):
        """
        Creates a dataframe containing statistics about different barcodes used
        """
        df = pd.DataFrame(columns=self.selection)
        for barcode in self.selection[:-1]:
            dico = {}
            file = open('statistics/{}'.format(barcode),'r')
            for line in file:
                key, value = line.strip().split('=')
                dico[key.strip()] = value.strip()
            file.close()
            df[barcode] = pd.Series(dico)
        df.to_csv('/home/ferrato/ownCloud/fast5_1D/dataframe.csv', header=self.selection_original,index=list(df.index), sep='\t')


