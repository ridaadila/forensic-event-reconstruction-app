import pandas as pd # type: ignore

class ForensicTimelineHelper():

    def filter_by_request(self, base_filename, source_filter, start_datetime, end_datetime):
        input_file = base_filename + '.csv'
        output_file = base_filename + '-fix.csv'

        data = pd.read_csv(input_file)

        data_filtered = data[
            (data['source_long'] != 'File stat') & 
            (data['source'].isin(source_filter))
        ]

        selected_data = data_filtered[['datetime', 'message']]
        selected_data_ori = data_filtered[['datetime', 'message', 'source']]

        selected_data['datetime'] = pd.to_datetime(selected_data['datetime'], errors='coerce')
        selected_data_ori['datetime'] = pd.to_datetime(selected_data_ori['datetime'], errors='coerce')

        if(start_datetime == '' and end_datetime == ''):
            selected_data.to_csv(output_file, index=False, header=False)
            selected_data_ori.to_csv(base_filename + '-original.csv', index=False)
            return
        
        start_datetime = pd.to_datetime(start_datetime)
        end_datetime = pd.to_datetime(end_datetime)

        valid_data_time_filtered = selected_data[
            (selected_data['datetime'] >= start_datetime) & 
            (selected_data['datetime'] <= end_datetime)
        ]

        valid_data_ori_time_filtered = selected_data_ori[
            (selected_data_ori['datetime'] >= start_datetime) & 
            (selected_data_ori['datetime'] <= end_datetime)
        ]

        valid_data_time_filtered.to_csv(output_file, index=False, header=False)
        valid_data_ori_time_filtered.to_csv(base_filename + '-original.csv', index=False)

    def clean_abstract_message(self, text):
        special_characters = "<>^"
        
        cleaned_text = text
        for char in special_characters:
            if isinstance(text, str):
                cleaned_text = cleaned_text.replace(char, "")
                return cleaned_text
            else:
                return "Unknown"

    def select_columns_used_for_episode_mining(self, base_filename): 
        df_ori = pd.read_csv(base_filename + '-mapping.csv')

        df_ori['epoch_time'] = None
        df_ori['cleaned_message'] = None

        df_ori['datetime'] = pd.to_datetime(df_ori['datetime'], format='mixed')

        df_ori['epoch_time'] = df_ori['datetime'].apply(lambda x: int(x.timestamp()))

        df_ori['cleaned_message'] = df_ori['abstract_message'].apply(self.clean_abstract_message)

        df_ori = df_ori[df_ori['cleaned_message'] != "Unknown"]

        df_ori = df_ori.sort_values(by='datetime')

        columns_to_save = ['datetime', 'epoch_time', 'source', 'cluster_id', 'abstract_message', 'cleaned_message', 'message']

        df_ori.to_csv(base_filename + '-selected_columns.csv', columns=columns_to_save, index=False)
        df_ori.to_csv(base_filename + '-mapping-edited.csv', columns=['datetime', 'cluster_id', 'source', 'message', 'abstract_message'], index=False)

    def convert_forensic_timeline_into_episode_mining_input_format(self, base_filename):
        csv_filename = base_filename + '-selected_columns.csv'
        txt_filename = base_filename + '-event-abstraction-for-episode.txt'
        df = pd.read_csv(csv_filename)

        epoch_time_clusters = df.groupby('epoch_time')['cluster_id'].apply(list).to_dict()

        sorted_epoch_clusters = sorted(epoch_time_clusters.items())
        result_df = pd.DataFrame(sorted_epoch_clusters, columns=['epoch_time', 'cluster_id'])

        result_df['cluster_id'] = result_df['cluster_id'].apply(lambda x: ' '.join(map(str, x)))
        result_df = result_df[['cluster_id', 'epoch_time']]

        result_df.to_csv(txt_filename, sep='|', header=False, index=False)