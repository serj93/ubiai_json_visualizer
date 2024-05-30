"""Построение графа из json-разметки в UbiAi"""
import argparse
import os
import sys
import graphviz

from typing import Optional
from helpers import read_file, loads_json, find_files
from morph import MystemTool


m = MystemTool()


class GraphBuilder:

    COLOR_COMPONENT = "#FFFFCC"
    COLOR_SYSTEM = "#66B2FF"
    COLOR_ATTR = "#E0E0E0"

    def printInventGraph(self, doc: dict, img_path: Optional[str] = None, is_view: bool = False):
        """Построение графа

        :param doc: словарь связей
        :param img_path: путь сохранения картинки
        :param is_view: отображать ли картинку
        :return:
        """
        tokens = doc.get('tokens')
        relations = doc.get('relations')

        # Define a graph
        doc_name = doc.get("documentName", "unknown")
        doc_text = doc.get("document", "unknown")

        if not img_path:
            img_path = f"./{doc_name}"

        dot = graphviz.Digraph(doc_name, filename=img_path, format="png")

        # default
        dot.attr(rankdir="LR", size="18")
        dot.attr("node", style="filled", fillcolor=self.COLOR_COMPONENT)
        dot.attr("node", shape="box")

        term_mapping = self._gen_term_mapper(tokens)

        # create nodes
        for index, entity in term_mapping.items():
            node = index
            prepared = self._prepare_node_name(entity['text'])
            label = f"<{prepared}>"
            entyty_type = entity['type']

            # отрисовываем компонеты
            if entyty_type == "SYSTEM":
                dot.node(node, label, shape="box3d", fillcolor=self.COLOR_SYSTEM)
            elif entyty_type == "ATTRIBUTE":
                dot.node(node, label, fillcolor=self.COLOR_ATTR)
            elif entyty_type == "COMPONENT":
                dot.node(node, label, fillcolor=self.COLOR_COMPONENT)
            else:
                # print(f"Ignore entity type {entyty_type}")
                continue

        edge_duplicate_filter = set()

        # create edges
        for rel in relations:
            rel: dict

            child_id = rel['child']
            head_id = rel['head']

            child_node = self._get_token_index(child_id, term_mapping)
            parent_node = self._get_token_index(head_id, term_mapping)
            rel_type = rel['relationLabel']

            # default label
            label = rel_type.lower()

            edge_fingerprint = f"{parent_node}_{label}_{child_node}"
            if edge_fingerprint in edge_duplicate_filter:
                continue
            else:
                edge_duplicate_filter.add(edge_fingerprint)

            if rel_type == "ATTRIBUTE-FOR":
                label = "attr-for"
                dot.edge(
                    parent_node,
                    child_node,
                    label=label,
                    style="dashed",
                    color="gray",
                )
            elif rel_type == "CONNECTED-WITH":
                dot.edge(
                    parent_node, child_node, label=label, color="black:invis:black"
                )
            elif rel_type == "LOCATED-AT":
                dot.edge(parent_node, child_node, label=label)
            else:
                dot.edge(parent_node, child_node, label=label, penwidth='2.0')

        # Now, let's add some general text under the graph
        doc_text_prepared = self._prepare_node_name(doc_text, line_after=10)
        general_text = f"<<B>{doc_name}</B><br/>{doc_text_prepared}>"

        # Append the general text to the label attribute of the graph
        dot.attr(label=general_text)

        dot.render(img_path, view=is_view, format='png', cleanup=True)

    def _get_token_index(self, token_id: int, mapper: dict) -> str:
        for index, data in mapper.items():
            for token_range in data['ranges']:
                if token_id in token_range:
                    return index

    def _gen_term_mapper(self, tokens: list) -> dict:
        mapper = {}
        for t in tokens:
            index = t['index']
            index_range = range(t['token_start'], t['token_end'] + 1)

            if index in mapper:
                item = mapper[index]
                if index_range not in item['ranges']:
                    item['ranges'].append(index_range)

            else:
                item = {
                    "text": t['text'],
                    "type": t['entityLabel'],
                    "ranges": [
                        index_range,
                    ],
                }
                mapper.update({index: item})

        return mapper

    def _prepare_node_name(self, name: str, line_after=3) -> str:
        words = name.split()
        prepared = ""
        for i, word in enumerate(words):
            # default
            is_break = i % line_after == 0
            is_break = False if i == 0 and line_after > 5 else is_break
            sep = "<br/>" if is_break else " "
            prepared += word + sep
        return prepared.strip()


def doc_preprocessing(doc: dict):
    """Обогащение данными."""
    for token in doc['tokens']:
        token_text_prep = token['text'].lower().strip().strip(',')
        token['text'] = token_text_prep
        token['index'] = get_lemma_index(token_text_prep)


def get_lemma_index(text: str) -> str:
    lemmas = m.lemmatize(text)
    result = [w for w in lemmas if w.strip()]
    return "_".join(result)


def process_files(input_dir, output_dir, file_pattern='*.json'):
    if not os.path.exists(input_dir):
        print(f"Ошибка: Директория ввода '{input_dir}' не существует.")
        sys.exit(1)

    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
        except OSError as e:
            print(f"Ошибка: не удалось создать директорию вывода '{output_dir}': {e}")
            sys.exit(1)

    path_pattern = os.path.join(input_dir, file_pattern)
    files = find_files(path_pattern)

    gbuilder = GraphBuilder()
    
    for filename in files:
        file_text = read_file(filename)

        data = loads_json(file_text)
        if not data:
            continue

        for doc in data:
            doc_name = doc.get("documentName", "unknown")
            img_path = os.path.join(output_dir, doc_name)
            doc_preprocessing(doc)
            gbuilder.printInventGraph(doc, img_path, is_view=False)



def main():
    parser = argparse.ArgumentParser(description='CLI для визуализации разметки UbiAI.')
    parser.add_argument('-i', '--input', required=True, help='Директория ввода')
    parser.add_argument('-o', '--output', required=True, help='Директория вывода')

    args = parser.parse_args()

    input_dir = args.input
    output_dir = args.output

    process_files(input_dir, output_dir)



if __name__ == '__main__':
    main()
