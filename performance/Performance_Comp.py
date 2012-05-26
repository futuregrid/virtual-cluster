#!/usr/bin/python

import argparse
import os

from pylab import *
from numpy import *

'''
Performance_Comp.py (python)
-------------------------

Creates charts for comparison of collected data

If data collected from Eucalyptus on india and
sierra are provided, a comparison graph
india-euca-sierra-euca will be produced.

If data collected from Eucaluptus and OpenStack
on india are provided, a comparsion graph
india-euca-india-nova will be prouced

Description

usage:

    python Performance_Plot.py <parameters>

    -in -- OpenStack raw data file collected on india
    -ie -- Eucalyptus raw data file collected on india
    -se -- Eucalyptus raw data file collected on sierra
    
    NOTE: Above data should be collected by performance tool
'''

class Performance_Plot():

    node_nums = [1, 2, 4, 8, 16, 24, 32]
    instance_types = ['small', 'medium', 'large']
    data = {'india-euca': {'small': {}, 'medium': {}, 'large': {}, 'data': False}, 
            'india-nova': {'small': {}, 'medium': {}, 'large': {}, 'data': False},
            'sierra-euca': {'small': {}, 'medium': {}, 'large': {}, 'data': False}}

    def process_data(self, india_euca, india_nova, sierra_euca):
        
        if not india_euca == None:
            if not os.path.isfile(os.path.expanduser(india_euca)):
                print "%s does not exist" % os.path.expanduser(india_euca)
                sys.exit()
            else:
                with open(os.path.expanduser(india_euca)) as input:
                    india_euca_content = input.readlines()
                self.fill_dict(india_euca_content, 'india-euca')
        if not india_nova == None:
            if not os.path.isfile(os.path.expanduser(india_nova)):
                print "%s does not exist" % os.path.expanduser(india_nova)
                sys.exit()
            else:
                with open(os.path.expanduser(india_nova)) as input:
                    india_nova_content = input.readlines()
                self.fill_dict(india_nova_content, 'india-nova')
        if not sierra_euca == None:
            if not os.path.isfile(os.path.expanduser(sierra_euca)):
                print "%s does not exist" % os.path.expanduser(sierra_euca)
                sys.exit()
            else:
                with open(os.path.expanduser(sierra_euca)) as input:
                    sierra_euca_content = input.readlines()
                self.fill_dict(sierra_euca_content, 'sierra-euca')

    def fill_dict(self, content, cloud):

        for line in content:
            values = line.split('\n')[0].split('\t')
            test_name = values[0].strip()
            
            if test_name.find('nova') >= 0 or test_name.find('euca') >= 0:
                if not self.get_node_num(test_name) in self.data[cloud][self.get_instance_type(test_name)]:
                    self.data[cloud]['data'] = True
                    self.data[cloud][self.get_instance_type(test_name)][self.get_node_num(test_name)] = {}
                    self.data[cloud][self.get_instance_type(test_name)][self.get_node_num(test_name)]['t_total'] = [float(values[1].strip())]
                else:
                    self.data[cloud][self.get_instance_type(test_name)][self.get_node_num(test_name)]['t_total'].append(float(values[1].strip()))
        
    def produce_graphs(self, args):

        self.process_data(args.india_euca, args.india_nova, args.sierra_euca)

        # Produce comparison graph about euca between india and sierra
        if self.data['india-euca']['data'] and self.data['sierra-euca']['data']:
            for instance_type in self.instance_types:
                self.produce_one_graph('india-euca',
                                       'sierra-euca',
                                       instance_type)
            

        # Produce comparison graph euca and openstack on india
        if self.data['india-euca']['data'] and self.data['india-nova']['data']:
            for instance_type in self.instance_types:
                self.produce_one_graph('india-euca',
                                       'india-nova',
                                       instance_type)

    def get_node_num(self, test_name):
        return int(test_name.split('-')[-1])
    
    def get_instance_type(self, test_name):
        return test_name.split('-')[-2].split('.')[-1]
    
    def get_cloud(self, test_name):
        return test_name.split('-')[0]
    
    def produce_one_graph(self, cloud1, cloud2, instance_type):

        processed_data = []
        x_label = []
        for node_num in self.node_nums:
            x_label.append('%s-%s' % (cloud1, node_num))
            x_label.append('%s-%s' % (cloud2, node_num))
            if node_num in self.data[cloud1][instance_type]:
                processed_data.append(self.data[cloud1][instance_type][node_num]['t_total'])
            else:
                processed_data.append([0])
            if node_num in self.data[cloud2][instance_type]:
                processed_data.append(self.data[cloud2][instance_type][node_num]['t_total'])
            else:
                processed_data.append([0])
    
        figure(figsize=(10,6))

        ax = gca()
        bp = ax.boxplot(processed_data, notch=0, sym='+', vert=1, whis=1.5)
        subplots_adjust(left=0.1, right=0.95, top=0.93, bottom=0.15)
        ax.yaxis.grid(True, linestyle='-', which='major', color='lightgrey', alpha=0.5)
        plt.setp(bp['boxes'], color='black')
        plt.setp(bp['whiskers'], color='black')
        plt.setp(bp['fliers'], color='red', marker='+')
        boxColors = ['darkkhaki','royalblue']

        data_size = len(x_label)
        medians = range(data_size)
        for i in range(data_size):
            box = bp['boxes'][i]
            boxX = []
            boxY = []
            for j in range(5):
                boxX.append(box.get_xdata()[j])
                boxY.append(box.get_ydata()[j])
            boxCoords = zip(boxX,boxY)

            k = i % 2
            boxPolygon = Polygon(boxCoords, facecolor=boxColors[k])
            ax.add_patch(boxPolygon)

            med = bp['medians'][i]
            medianX = []
            medianY = []
            for j in range(2):
                medianX.append(med.get_xdata()[j])
                medianY.append(med.get_ydata()[j])
                plt.plot(medianX, medianY, 'k')
                medians[i] = medianY[0]
                plt.plot([average(med.get_xdata())], [average(processed_data[i])],
                         color='w', marker='*', markeredgecolor='k')

        xtickNames = plt.setp(ax, xticklabels=x_label)
        plt.setp(xtickNames, rotation=30, fontsize=8)
        ax.set_title('%s VS %s at %s-instances: Total setup time' % (cloud1, cloud2, instance_type))
        ax.set_xlabel('Cloud - Host - Node Number')
        ax.set_ylabel('Time (Seconds)')
        ax.set_axisbelow(True)

        # add lengend
        figtext(0.15, 0.85, cloud1,
                backgroundcolor=boxColors[0],
                color='black',
                weight='roman',
                size='x-small')
        figtext(0.15, 0.815, cloud2,
                backgroundcolor=boxColors[1],
                color='white',
                weight='roman',
                size='x-small')
        figtext(0.15, 0.780, '*',
                color='white',
                backgroundcolor='silver',
                weight='roman',
                size='medium')
        figtext(0.165, 0.785, ' Average Value',
                color='black',
                weight='roman',
                size='x-small')

        savefig('%s-%s-%s.png' % (cloud1, cloud2, instance_type))

def main():
    PP = Performance_Plot()
    parser = argparse.ArgumentParser(description='Performance test tool -- Draw comparison graph')
    parser.add_argument('-in', '--india-nova', action='store',
                        help='Performance test raw data on india using OpenStack')
    parser.add_argument('-ie', '--india-euca', action='store',
                        help='Performance test raw data on india using Eucalyptus')
    parser.add_argument('-se', '--sierra-euca', action='store',
                        help='Performance test raw data on sierra using Eucalyptus')
    parser.set_defaults(func=PP.produce_graphs)
    args = parser.parse_args()
    args.func(args)

if __name__ == '__main__':
    main()