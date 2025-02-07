from spmf import Spmf # type: ignore
import pandas as pd # type: ignore

class EpisodeMining():

    def run(self, base_filename, minsup, algo):
        txt_filename = base_filename + '-event-abstraction-for-episode.txt'
        winlen = 45
        output_filename = "output-" + base_filename + "-" + algo + "-minsup-" + str(minsup) + ".txt"
        spmf = Spmf(algo, input_filename=txt_filename,
                    output_filename=output_filename, spmf_bin_location_dir="./", arguments=[minsup, winlen, 0])
        spmf.run()
        return output_filename

    def extract_output_spmf_to_list(self, input_filename):
        df = pd.read_csv(input_filename, header=None)
        
        event_set_result = []
        support_result = []
        for i in range(len(df)):
            row_content = str(df.iloc[i, 0])  
            list_of_content = row_content.split(" #SUP: ")
            support = int(list_of_content[len(list_of_content)-1])
            event_set = list_of_content[0]
            
            list_event_set = event_set.split(" ")
            list_event_set_final = [int(value) for value in list_event_set if value != '-1']
            
            event_set_result.append(list_event_set_final)
            support_result.append(support)
            
        reversed_list = [sublist for sublist in event_set_result[::-1] if len(sublist) > 1]
        sorted_list = sorted(reversed_list, key=len, reverse=True)
        
        return sorted_list
    
    def assign_case_id_to_events(self, events, traces):
        # Case ID awal
        case_id = 1

        events_with_ids = [(event, None) for event in events]

        for trace in traces:
            print("trace: ", trace)

            for i in range(len(events) - len(trace) + 1):
                if [event[0] for event in events_with_ids[i:i+len(trace)]] == trace:
                    if all(event[1] is not None for event in events_with_ids[i:i+len(trace)]):
                        continue

                    for j in range(len(trace)):
                        events_with_ids[i + j] = (events_with_ids[i + j][0], case_id)
                        print("event: ", events_with_ids[i + j][0], ", case id: ", case_id)

                    case_id += 1

        list_of_case_id = []
        for event in events_with_ids:
            if event[1] is None:
                list_of_case_id.append(case_id)
                case_id += 1
            else:
                list_of_case_id.append(event[1])

        return list_of_case_id
    

    def create_df_with_case_id(self, base_filename, list_of_traces):
        csv_filename = base_filename + '-selected_columns.csv'
        df_ori = pd.read_csv(csv_filename)
        df_ori = df_ori.sort_values(by=['datetime'], ascending=[True])
        cluster_id_list = df_ori['cluster_id'].tolist()
        list_case_id = self.assign_case_id_to_events(cluster_id_list, list_of_traces)
        df_ori['case_id'] = list_case_id
        df_ori['case_id'] = df_ori['case_id'].astype(int)
        df_ori.to_csv(base_filename + "-with-case-id.csv")
        return df_ori
