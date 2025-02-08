import pm4py # type: ignore
from pm4py.algo.conformance.tokenreplay import algorithm as token_replay # type: ignore
from pm4py.algo.conformance.alignments.petri_net import algorithm as alignments # type: ignore
from pm4py.algo.evaluation.replay_fitness import algorithm as replay_fitness_evaluator # type: ignore
from pm4py.algo.evaluation.precision import algorithm as precision_evaluator # type: ignore
from pm4py.algo.evaluation.generalization import algorithm as generalization_evaluator # type: ignore
from pm4py.algo.evaluation.simplicity import algorithm as simplicity_evaluator # type: ignore

class ProcessMining():

    def format_df_into_pm4py_event_log(self, df):
        event_log = pm4py.format_dataframe(df, case_id='case_id', activity_key='cleaned_message', timestamp_key='datetime')
        return event_log

    def get_num_of_events(self, df):
        num_events = len(df)
        return num_events
    
    def get_num_of_events_and_case(self, df):
        num_cases = len(df.case_id.unique())
        return num_cases

    def get_start_activities(self, event_log):
        start_activities = pm4py.get_start_activities(event_log)
        return start_activities
    
    def get_end_activities(self, event_log): 
        end_activities = pm4py.get_end_activities(event_log)
        return end_activities 
    
    def generate_petri_net_heuristics(self, event_log, base_filename, rankdir):
        vis_filename = "static/images/" + base_filename + '-petri-net-heuristics.jpeg'
        net_heuristics, initial_marking_heuristics, final_marking_heuristics = pm4py.discover_petri_net_heuristics(event_log)
        pm4py.save_vis_petri_net(net_heuristics, initial_marking_heuristics, final_marking_heuristics, 
                          vis_filename, rankdir=rankdir)
        
        return net_heuristics, initial_marking_heuristics, final_marking_heuristics
        
    def generate_petri_net_alpha(self, event_log, base_filename, rankdir):
        vis_filename = "static/images/" + base_filename + '-petri-net-alpha.jpeg'
        net_alpha, initial_marking_alpha, final_marking_alpha = pm4py.discover_petri_net_alpha(event_log)
        pm4py.save_vis_petri_net(net_alpha, initial_marking_alpha, final_marking_alpha, vis_filename, rankdir=rankdir)

        return net_alpha, initial_marking_alpha, final_marking_alpha

    def generate_petri_net_inductive_miner(self, event_log, base_filename, rankdir):
        vis_filename = "static/images/" + base_filename + '-petri-net-inductive-miner.jpeg'
        net_inductive, initial_marking_inductive, final_marking_inductive = pm4py.discover_petri_net_inductive(event_log)
        pm4py.save_vis_petri_net(net_inductive, initial_marking_inductive, final_marking_inductive, vis_filename, rankdir=rankdir)

        return net_inductive, initial_marking_inductive, final_marking_inductive

    def generate_petri_net_ilp_miner(self, event_log, base_filename, rankdir):
        vis_filename = "static/images/" + base_filename + '-petri-net-ilp-miner.jpeg'
        net_ilp, initial_marking_ilp, final_marking_ilp = pm4py.discover_petri_net_ilp(event_log)
        pm4py.save_vis_petri_net(net_ilp, initial_marking_ilp, final_marking_ilp, vis_filename, rankdir=rankdir)

        return net_ilp, initial_marking_ilp, final_marking_ilp

    def convert_to_bpmn(self, base_filename, net, initial_marking, final_marking, vis_filename):
        vis_filename = "static/images/" + base_filename + '-bpmn-model.jpeg'
        bpmn_model = pm4py.convert_to_bpmn(net, initial_marking, final_marking)
        pm4py.save_vis_bpmn(bpmn_model, vis_filename)

    def get_token_replay_results(self, results):
        print("-----------------------------TOKEN REPLAY-------------------------------------------")
        for i, result in enumerate(results):
            print(f"Trace {i + 1}:")
            print(f"  Trace is fit: {result['trace_is_fit']}")
            print(f"  Trace fitness: {result['trace_fitness']}")
            print("  Activated transitions:")
            for transition in result['activated_transitions']:
                print(f"    {transition}")
            print(f"  Reached marking: {result['reached_marking']}")
            print(f"  Enabled transitions in marking: {result['enabled_transitions_in_marking']}")
            print(f"  Transitions with problems: {result['transitions_with_problems']}")
            print(f"  Missing tokens: {result['missing_tokens']}")
            print(f"  Consumed tokens: {result['consumed_tokens']}")
            print(f"  Remaining tokens: {result['remaining_tokens']}")
            print(f"  Produced tokens: {result['produced_tokens']}")
            print("-" * 40)

    def get_alignment_results(self, results):
        output = []
        alignment_text = "ALIGNMENTS"
        output.append(alignment_text.center(80))  # Menyusun teks agar rata tengah dengan panjang 80 karakter
        output.append("\n")
        
        for index, data in enumerate(results):
            output.append(f"Trace {index + 1}:\n")
            counter = 1

            if 'alignment' in data:
                for align in data['alignment']:
                    event_log_align = align[0]
                    model_process_align = align[1]
                    output.append(f"  {counter}) Event log= {event_log_align} | Model process= {model_process_align}\n")
                    counter += 1
            
            output.append("---------------\n")
            output.append(f"Cost: {data['cost']}\n")
            output.append("---------------\n")
            output.append(f"Visited states: {data['visited_states']}\n")
            output.append("---------------\n")
            output.append(f"Queued states: {data['queued_states']}\n")
            output.append("---------------\n")
            output.append(f"Traversed arcs: {data['traversed_arcs']}\n")
            output.append("---------------\n")
            output.append(f"LP solved: {data['lp_solved']}\n")
            output.append("---------------\n")
            output.append(f"Fitness: {data['fitness']}\n")
            output.append("---------------\n")
            output.append(f"BWC: {data['bwc']}\n")
            output.append("------------------------------------------------------------------------------------------\n")
        
        return "".join(output)


    def get_fitness(self, event_log, net, initial_marking, final_marking):
        fitness = replay_fitness_evaluator.apply(event_log, net, initial_marking, final_marking, 
                                         variant=replay_fitness_evaluator.Variants.ALIGNMENT_BASED)
        return fitness
    
    def get_precision(self, event_log, net, initial_marking, final_marking):
        precision = precision_evaluator.apply(event_log, net, initial_marking, final_marking, 
                                           variant=precision_evaluator.Variants.ALIGN_ETCONFORMANCE)
        return precision
    
    def get_generalization(self, event_log, net, initial_marking, final_marking):
        generalization = generalization_evaluator.apply(event_log, net, initial_marking, final_marking)
        return generalization
    
    def get_simplicity(self, net): 
        simplicity = simplicity_evaluator.apply(net)
        return simplicity 
    
    def get_alignment(self, event_log, net, initial_marking, final_marking):
        aligned_traces = alignments.apply(event_log, net, initial_marking, final_marking)
        return self.get_alignment_results(aligned_traces)
    
    def get_replayed_traces(self, event_log, net, initial_marking, final_marking):
        replayed_traces = token_replay.apply(event_log, net, initial_marking, final_marking)
        self.get_token_replay_results(replayed_traces)