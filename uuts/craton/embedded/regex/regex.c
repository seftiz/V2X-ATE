/*
 *  regex.c
 *
 *  Regular expression library
 *
 *  Copyright (C) 2007 Mohammad Mohsenzadeh <mmohsenz@gmail.com>
 *
 *  This library is free software; you can redistribute it and/or
 *  modify it under the terms of the GNU Lesser General Public
 *  License as published by the Free Software Foundation; either
 *  version 2.1 of the License, or (at your option) any later version.
 *
 *  This library is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
 *  Lesser General Public License for more details.
 *
 *  You should have received a copy of the GNU Lesser General Public
 *  License along with this library; if not, write to the Free Software
 *  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA 
 *
 *
 *  20 Jun 2007: Mohammad Mohsenzadeh <mmohsenz@gmail.com>
 *          - Pre-alpha release
 */

#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <ctype.h>
#include <stdint.h>

#include "vector.h"
#include "regex.h"

#define REGEX_MALLOC malloc
#define REGEX_FREE free
#define REGEX_PRINT printf

#ifdef DEBUG
#define DEBUGP REGEX_PRINT
#else
#define DEBUGP(format, args...)
#endif

enum nfa_opcode {
	NFA_NONE = 0,
	NFA_BOL,
	NFA_EOL,
	NFA_CHAR,
	NFA_FREE
};

struct nfa_transition {
	struct vector_node list;
	enum nfa_opcode type;

	struct {
		uint8_t lo;
		uint8_t hi;
	} alpha;

	struct nfa_state *next;
};    

struct nfa_state {
	struct vector_node list;
	struct vector_node set;

	uint32_t id;
	uint8_t final;

	struct vector_head table;
};

struct nfa {
	struct vector_node list;

	struct nfa_state *start;
	struct nfa_state *end;

	struct vector_head states;
};

struct nfa_set {
	uint8_t size;
	struct nfa_state **head;
};

struct dfa_state {
	struct vector_node list;

	uint32_t id;
	uint8_t final;

	struct nfa_set *nfa;

	struct {
		struct dfa_state *next;
	} table[REG_MAGIC];
};

struct dfa {
	struct dfa_state *start;

	struct vector_head states;
};

static void
nfa_print (struct nfa *nfa)
{
	struct nfa_state *pos;
	struct nfa_transition *trans;

	REGEX_PRINT ("\tsubgraph nfa {\n");
	vector_iterate_entry (pos, &nfa->states, list) {
		vector_iterate_entry  (trans, &pos->table, list) {
			switch (trans->type) {
				case NFA_CHAR:
					if (trans->alpha.lo == trans->alpha.hi) {
						if (isprint (trans->alpha.lo))
							REGEX_PRINT ("\t\tn%u -> n%u [label = \"%c\"]\n",
										 pos->id, trans->next->id,
										 trans->alpha.lo);
						else
							REGEX_PRINT ("\t\tn%u -> n%u [label = \"%d\"]\n",
										 pos->id, trans->next->id,
										 trans->alpha.lo);
					}
					else {
						if (trans->alpha.lo >= 32 && trans->alpha.hi <= 126)
							REGEX_PRINT ("\t\tn%u -> n%u [label = \"%c-%c\"]\n",
										 pos->id, trans->next->id,
										 trans->alpha.lo, trans->alpha.hi);
						else
							REGEX_PRINT ("\t\tn%u -> n%u [label = \"%d-%d\"]\n",
										 pos->id, trans->next->id,
										 trans->alpha.lo, trans->alpha.hi);
					}
					break;

				case NFA_FREE:
					REGEX_PRINT ("\t\tn%u -> n%u [label = \"FREE\"]\n",
								 pos->id, trans->next->id);
					break;

				default:
					break;
			}
		}
		if (pos->final)
			REGEX_PRINT ("\t\tn%u [shape=doublecircle]\n", pos->id);
	}
	REGEX_PRINT ("\t}\n");
}

static void
dfa_print (struct dfa *dfa)
{
	struct dfa_state *pos;
	unsigned int i;

	REGEX_PRINT ("\tsubgraph dfa {\n");

	if (dfa->start->final)
		REGEX_PRINT ("\t\td%d [shape=doublecircle];\n", dfa->start->id);

	vector_iterate_entry (pos, &dfa->states, list)
		for (i = 0; i < REG_MAGIC; i++)
			if (pos->table[i].next) {
				if (isprint (i))
					REGEX_PRINT ("\t\td%d -> d%d [label = \"%c\"];\n",
							pos->id, pos->table[i].next->id, i);
				else
					REGEX_PRINT ("\t\td%d -> d%d [label = \"%d\"];\n",
							pos->id, pos->table[i].next->id, i);

				if (pos->table[i].next->final)
					REGEX_PRINT ("\t\td%d [shape=doublecircle];\n",
							pos->table[i].next->id);
			}

	REGEX_PRINT ("\t}\n");
}

static inline struct nfa_transition *
nfa_trans_alloc (struct nfa_state *entry, struct nfa_state *next,
                 enum nfa_opcode type, uint8_t lo, uint8_t hi)
{
	struct nfa_transition *t;

	t = REGEX_MALLOC (sizeof (struct nfa_transition));
	if (!t)
		return NULL;

	t->type = type;
	t->alpha.lo = lo;
	t->alpha.hi = hi;
	t->next = next;
	vector_add_tail (&t->list, &entry->table);
	return t;
}

static inline struct nfa_state *
nfa_state_alloc (struct vector_head *head)
{
	static unsigned int nfa_state_next_id = 0;
	struct nfa_state *s;

	s = REGEX_MALLOC (sizeof (struct nfa_state));
	if (!s)
		return NULL;

	s->id = nfa_state_next_id++;
	s->final = 0;
	vector_head_init (&s->table);
	vector_add_tail (&s->list, head);
	return s;
}

static inline void
nfa_state_free (struct nfa_state *entry)
{
	struct nfa_transition *pos, *n;
	vector_iterate_entry_safe (pos, n, &entry->table, list) {
		vector_del (&pos->list);
		REGEX_FREE (pos);
	}
	REGEX_FREE (entry);
}

static inline void
nfa_free (struct nfa *entry)
{
	struct nfa_state *pos, *n;
	vector_iterate_entry_safe (pos, n, &entry->states, list) {
		vector_del (&pos->list);
		nfa_state_free (pos);
	}
	REGEX_FREE (entry);
}

static inline struct nfa *
nfa_alloc (enum nfa_opcode type, uint8_t lo, uint8_t hi)
{
	struct nfa *n;

	n = REGEX_MALLOC (sizeof (struct nfa));
	if (!n)
		return NULL;

	vector_head_init (&n->states);

	n->start = nfa_state_alloc (&n->states);
	n->end = nfa_state_alloc (&n->states);
	if (!n->start || !n->end)
		goto err_out_free_new;

	if (type != NFA_NONE)
		if (!nfa_trans_alloc (n->start, n->end, type, lo, hi))
			goto err_out_free_new;

	return n;

err_out_free_new:
	nfa_free (n);
	return NULL;
}

#define PATFETCH(c) (c = pat[(*i)++])
#define PATUNFETCH(c) (c = pat[--(*i) - 1])

enum regex_token {
	REG_BEGIN = 1,
	REG_BOL,
	REG_EOL,
	REG_RPT,
	REG_RPAREN,
	REG_RBRACE,
	REG_RBRACK,
	REG_ANY,
	REG_CSET,
	REG_CHAR
};

static struct nfa *
nfa_handle_alter (struct nfa *n1, struct nfa *n2)
{
	struct nfa_state *s;

	s = nfa_state_alloc (&n1->states);
	if (!s)
		return NULL;

	if (!nfa_trans_alloc (n1->start, n2->start, NFA_FREE, 0, 0)
			|| !nfa_trans_alloc (n1->end, s, NFA_FREE, 0, 0)
			|| !nfa_trans_alloc (n2->end, s, NFA_FREE, 0, 0)) {
		nfa_state_free (s);
		return NULL;
	}

	n1->end = s;
	vector_movel_tail (n2->states.first, n2->states.last, &n1->states);
	nfa_free (n2);
	return n1;
}

static inline struct nfa *
__nfa_handle_concat (struct nfa *n1, struct nfa *n2)
{
	if (!nfa_trans_alloc (n1->end, n2->start, NFA_FREE, 0, 0))
		return NULL;
	n1->end = n2->end;
	vector_movel_tail (n2->states.first, n2->states.last, &n1->states);
	nfa_free (n2);
	return n1;
}

static inline int
nfa_handle_concat (struct vector_head *stack)
{
	struct nfa *cur, *next;

	vector_iterate_entry_safe (next, cur, stack, list) {
		if (&cur->list == (struct vector_node *)stack)
			break;

		vector_del (&next->list);
		
		if (!__nfa_handle_concat (cur, next))
			return REG_ESPACE;
	}
	return 0;
}

#define CHAR_CLASS_MAX_LENGTH 6

static struct nfa *
nfa_handle_cset (const char *pat, unsigned int len, unsigned int *i,
                 int cflags, int *errp)
{
	struct nfa *n;
	enum regex_token last_token = REG_RBRACK;
	uint8_t field[256], mark = 1;
	unsigned int j;
	uint8_t c;
	int lo = -1;

	PATFETCH (c);
	if (*i >= len) {
		*errp = REG_EBRACK;
		return NULL;
	}

	if (c == '^') {
		mark = 0;
		PATFETCH (c);
	}
	memset (field, !mark, sizeof (uint8_t) * 256);

	do {
		if (*i >= len) {
			*errp = REG_EBRACK;
			return NULL;
		}

		if (c == '[') {
			if (*i >= len) {
				*errp = REG_EBRACK;
				return NULL;
			}
			PATFETCH (c);
			switch (c) {
				case '.':
					break;
				case '=':
					break;
				case ':':
					{
						char cclass[CHAR_CLASS_MAX_LENGTH + 1];

						for (j = 0; j < CHAR_CLASS_MAX_LENGTH; j++) {
							PATFETCH (c);
							if (*i < len && c == ':' && pat[*i] == ']') {
								PATFETCH (c);
								break;
							}
							cclass[j] = c;
						}
						cclass[j] = '\0';
					
						{
							uint8_t calnum = (strcmp (cclass, "alnum") == 0);
							uint8_t calpha = (strcmp (cclass, "alpha") == 0);
							uint8_t ccntrl = (strcmp (cclass, "cntrl") == 0);
							uint8_t cdigit = (strcmp (cclass, "digit") == 0);
							uint8_t cgraph = (strcmp (cclass, "graph") == 0);
							uint8_t clower = (strcmp (cclass, "lower") == 0);
							uint8_t cprint = (strcmp (cclass, "print") == 0);
							uint8_t cpunct = (strcmp (cclass, "punct") == 0);
							uint8_t cspace = (strcmp (cclass, "space") == 0);
							uint8_t cupper = (strcmp (cclass, "upper") == 0);
							uint8_t cxdigit = (strcmp (cclass, "xdigit") == 0);

							if ((cflags & REG_ICASE) && (clower || cupper))
								calpha = 1;

							for (j = 0; j < 256; j++)
								if ((calnum && isalnum (j))
										|| (calpha && isalpha (j))
										|| (ccntrl && iscntrl (j))
										|| (cdigit && isdigit (j))
										|| (cgraph && isgraph (j))
										|| (clower && islower (j))
										|| (cprint && isprint (j))
										|| (cpunct && ispunct (j))
										|| (cspace && isspace (j))
										|| (cupper && isupper (j))
										|| (cxdigit && isxdigit (j)))
									field[j] = mark;
						}
					}
					break;

				default:
					PATUNFETCH (c);
					goto skip_subbracket;
			}
			last_token = REG_CSET;
			goto skip_all;
		}

skip_subbracket:
		if (last_token != REG_RBRACK && c == '-'
				&& *i < len && pat[*i] != ']') {
			if (last_token != REG_CHAR) {
				*errp = REG_ERANGE;
				return NULL;
			}

			PATFETCH (c);
			if (pat[*i - 3] > c) {
				*errp = REG_ERANGE;
				return NULL;
			}

			for (j = pat[*i - 3]; j <= c; j++) {
				field[j] = mark;
				if ((cflags & REG_ICASE) && isalpha (c))
					field[(islower (c) ? toupper (c) : tolower (c))] = mark;
			}
			last_token = REG_CSET;
		}
		else {
			field[c] = mark;
			if ((cflags & REG_ICASE) && isalpha (c))
				field[(islower (c) ? toupper (c) : tolower (c))] = mark;
			last_token = REG_CHAR;
		}
skip_all:
		PATFETCH (c);
	} while (c != ']');

	n = nfa_alloc (NFA_NONE, 0, 0);
	if (!n) {
		*errp = REG_ESPACE;
		return NULL;
	}

	for (j = 0; j < 256; j++) {
		if (field[j] && lo < 0)
			lo = j;
		else if (!field[j] && lo >= 0) {
			if (!nfa_trans_alloc (n->start, n->end, NFA_CHAR, lo, j - 1))
				goto err_out_free_cset;
			lo = -1;
		}
	}
	if (lo >= 0 && !nfa_trans_alloc (n->start, n->end, NFA_CHAR, lo, j - 1))
		goto err_out_free_cset;

	return n;

err_out_free_cset:
	*errp = REG_ESPACE;
	nfa_free (n);
	return NULL;
}

static struct nfa *
__nfa_compile (const char *pat, unsigned int len, unsigned int *i,
               int nsubs, int cflags, int *errp)
{
	VECTOR_HEAD (stack);
	enum regex_token last_token = REG_BEGIN;
	struct vector_node *pos, *n;
	struct nfa *nfa;
	uint8_t c;
	int escaped = 0;

#define STACK_PUSH(new) vector_add (&new->list, &stack)
#define STACK_PEEK() vector_entry (stack.first, struct nfa, list)

	while (*i < len) {
		PATFETCH (c);
		switch (c) {
			case ')':
				if ((!(cflags & REG_EXTENDED) ^ escaped) || (nsubs <= 0))
					goto normal_char;
				goto nfa_compile_done;

			case '\\':
				if (escaped)
					goto normal_char;
				escaped = 1;
				continue;

			case '^':
				if (escaped)
					goto normal_char;
				//last_token = REG_BOL;
				break;

			case '$':
				if (escaped)
					goto normal_char;
				//last_token = REG_EOL;
				break;

			case '|':
				if (!(cflags & REG_EXTENDED) ^ escaped)
					goto normal_char;
				else if (!(cflags & REG_EXTENDED) && escaped) {
					*errp = REG_EESCAPE;
					goto err_out_free_stack;
				}

				if (last_token == REG_BEGIN || last_token == REG_BOL) {
					*errp = REG_BADPAT;
					goto err_out_free_stack;
				}

				nfa_handle_concat (&stack);
				nfa = STACK_PEEK ();
				{
					struct nfa *nfa2;
					nfa2 = __nfa_compile (pat, len, i, nsubs, cflags, errp);
					if (!nfa2)
						goto err_out_free_stack;

					if (!nfa_handle_alter (nfa, nfa2)) {
						nfa_free (nfa2);
						goto err_out_of_memory;
					}
				}
				return nfa;

			case '(':
				if ((cflags & REG_EXTENDED) ^ escaped) {
					nfa = __nfa_compile (pat, len, i, nsubs + 1, cflags, errp);
					if (!nfa)
						goto err_out_free_stack;
					STACK_PUSH (nfa);
					last_token = REG_RPAREN;
					break;
				}
				goto normal_char;
				break;

			case '[':
				if (escaped)
					goto normal_char;

				nfa = nfa_handle_cset (pat, len, i, cflags, errp);
				if (!nfa)
					goto err_out_free_stack;
				STACK_PUSH (nfa);
				last_token = REG_CSET;
				break;

			case '{':
				if ((cflags & REG_EXTENDED) ^ escaped) {

					if (last_token == REG_BEGIN || last_token == REG_BOL) {
						*errp = REG_BADRPT;
						goto err_out_free_stack;
					}

					last_token = REG_RPT;
					*errp = REG_BADPAT;
					goto err_out_free_stack;
					break;
				}
				goto normal_char;
				break;

			case '+':
			case '?':
				if (!(cflags & REG_EXTENDED))
					goto default_char;
			case '*':
				if (escaped)
					goto normal_char;

				if (last_token == REG_BEGIN || last_token == REG_BOL
						|| last_token == REG_RPT) {
					*errp = REG_BADRPT;
					goto err_out_free_stack;
				}

				nfa = STACK_PEEK ();
				if (c == '+' &&
						!nfa_trans_alloc (nfa->end, nfa->start, NFA_FREE, 0, 0))
					goto err_out_of_memory;

				else if (c == '?' &&
						!nfa_trans_alloc (nfa->start, nfa->end, NFA_FREE, 0, 0))
					goto err_out_of_memory;

				else if (c == '*') {
					if (!nfa_trans_alloc (nfa->end, nfa->start, NFA_FREE, 0, 0))
						goto err_out_of_memory;
					nfa->end = nfa->start;
				}

				last_token = REG_RPT;
				break;

			case '.':
				if (escaped)
					goto normal_char;

				nfa = nfa_alloc (NFA_CHAR, 0, 255);
				if (!nfa)
					goto err_out_of_memory;
				STACK_PUSH (nfa);
				last_token = REG_ANY;
				break;

			case 'x':
				if (!escaped)
					goto normal_char;

				if (*i + 1 >= len) {
					*errp = REG_EEND;
					goto err_out_free_stack;
				}

				{
					uint8_t j, hex = 0;

					for (j = 0; j < 2; j++) {
						hex = hex << 4;

						PATFETCH (c);
						if (!isxdigit (c)) {
							*errp = REG_BADPAT;
							goto err_out_free_stack;
						}

						hex += (isdigit (c) ? (c - 48) : (tolower (c) - 97));
					}
					c = hex;
				}
				goto normal_char;

			default:
default_char:
				if (escaped) {
					if (c == 'n')
						c = '\n';
					else if (c == 't')
						c = '\t';
					else if (c == 'r')
						c = '\r';
					else if (c == 'v')
						c = '\v';
					else if (c == 'a')
						c = '\a';
					else if (c == 'b')
						c = '\b';
					else {
						*errp = REG_EESCAPE;
						goto err_out_free_stack;
					}
				}

normal_char:
				nfa = nfa_alloc (NFA_CHAR, c, c);
				if (!nfa)
					goto err_out_of_memory;
				STACK_PUSH (nfa);

				if ((cflags & REG_ICASE) && isalpha (c)) {
					c = (islower (c) ? toupper (c) : tolower (c));
					if (!nfa_trans_alloc (nfa->start, nfa->end, NFA_CHAR, c, c))
						goto err_out_of_memory;
				}
				last_token = REG_CHAR;
		}
		escaped = 0;
	}

	if (escaped) {
		*errp = REG_EESCAPE;
		goto err_out_free_stack;
	}
	else if (nsubs > 0) {
		*errp = REG_EPAREN;
		goto err_out_free_stack;
	}

nfa_compile_done:
	if (last_token == REG_BEGIN || last_token == REG_BOL) {
		*errp = REG_EEND;
		goto err_out_free_stack;
	}

	nfa_handle_concat (&stack);
	return vector_entry(stack.first, struct nfa, list);

err_out_of_memory:
	*errp = REG_ESPACE;
err_out_free_stack:
	vector_iterate_safe (pos, n, &stack) {
		vector_del (pos);
		nfa_free (vector_entry (pos, struct nfa, list));
	}
	return NULL;
}

static struct nfa *
nfa_compile (const char *pattern,
             unsigned int pattern_len,
			 uint8_t retcode,
             int cflags, int *errp)
{
	struct nfa *start, *big;
	unsigned int index = 0;

	big = __nfa_compile (pattern, pattern_len, &index, 0, cflags, errp);
	if (!big)
		return NULL;

	big->end->final = retcode;

	index = 0;
	if (pattern[index] == '^')
		return big;

	start = __nfa_compile (".*", 2, &index, 0, cflags, errp);
	if (!start)
		goto err_out_free_big;

	start = __nfa_handle_concat (start, big);
	if (!start)
		goto err_out_free_start;
	return start;

err_out_free_start:
	nfa_free (start);
err_out_free_big:
	nfa_free (big);
	return NULL;
}

static unsigned int
__nfa_step (struct nfa_state *src, struct vector_head *head)
{
	struct nfa_state *pos;
	struct nfa_transition *trans;
	unsigned int length = 0;
	uint8_t added = 0;

	vector_iterate_entry (pos, head, set) {
		if (pos->id == src->id)
			return length;
		else if (pos->id > src->id)
			break;
	}
	vector_add_tail (&src->set, (struct vector_head *)&pos->set);
	length++;

	vector_iterate_entry (trans, &src->table, list)
		if (trans->type == NFA_FREE)
			length += __nfa_step (trans->next, head);

	return length;
}

static inline struct nfa_set *
nfa_step (const struct nfa_set *src, unsigned short chr, int *errp)
{
	VECTOR_HEAD (head);
	struct nfa_state *pos;
	struct nfa_set *new;
	struct nfa_transition *trans;
	unsigned int size = 0;
	unsigned int i;

	for (i = 0; i < src->size; i++) {
		vector_iterate_entry (trans, &src->head[i]->table, list) {
			if (chr == REG_MAGIC) {
				size += __nfa_step (src->head[i], &head);
				break;
			}
			else if (trans->type == NFA_CHAR
					&& trans->alpha.lo <= chr && trans->alpha.hi >= chr)
				size += __nfa_step (trans->next, &head);
		}
	}

	if (!size)
		return NULL;

	new = REGEX_MALLOC (sizeof (struct nfa_set) 
			+ sizeof (unsigned long) * size);
	if (!new) {
		*errp = REG_ESPACE;
		return NULL;
	}

	new->size = size;
	new->head = (struct nfa_state **)(new + 1);
	vector_iterate_entry_reverse (pos, &head, set)
		new->head[--size] = pos;
	return new;
}

static inline struct dfa_state *
dfa_state_alloc (struct nfa_set *nfa)
{
	static unsigned int dfa_state_next_id = 0;
	struct dfa_state *new;
	unsigned int i;

	new = REGEX_MALLOC (sizeof (struct dfa_state));
	if (!new)
		return NULL;

	memset (new, 0, sizeof (struct dfa_state));
	new->id = dfa_state_next_id++;
	new->nfa = nfa;

	for (i = 0; i < nfa->size; i++) {
		if (nfa->head[i]->final) {
			new->final = nfa->head[i]->final;
			break;
		}
	}

#ifdef DEBUG
	REGEX_PRINT ("d%u:", new->id);
	for (i = 0; i < nfa->size; i++)
		REGEX_PRINT (" n%u%s", nfa->head[i]->id,
				(nfa->head[i]->final ? "(*)": ""));
	REGEX_PRINT ("\n");
#endif

	return new;
}

static int
__dfa_compile (struct dfa_state *dst,
               struct nfa_set *src,
               struct vector_head *head)
{
	struct nfa_set *set;
	struct dfa_state *pos;
	unsigned int i, j;
	int ret = 0;
	int dup;

	for (i = 0; i < 256; i++) {
		//    for (i = 32; i < 123; i++) {
		set = nfa_step (src, i, &ret);
		if (!set) {
			if (ret)
				goto err_out_free_dfa;
			continue;
		}

		dup = 0;
		vector_iterate_entry (pos, head, list) {
			if (set->size != pos->nfa->size)
				continue;

			dup = 1;
			for (j = 0; j < set->size; j++)
				if (pos->nfa->head[j]->id != set->head[j]->id) {
					dup = 0;
					break;
				}

			if (dup) {
				REGEX_FREE (set);
				dst->table[i].next = pos;
				break;
			}
		}

		if (dup)
			continue;

		dst->table[i].next = dfa_state_alloc (set);
		if (!dst->table[i].next)
			goto err_out_free_dfa;

		vector_add_tail (&dst->table[i].next->list, head);

//		if (!dst->table[i].next->final)
			__dfa_compile (dst->table[i].next, set, head);
	}
	return 0;

err_out_free_dfa:
	return REG_ESPACE;
}

static struct dfa *
dfa_compile (struct nfa *nfa, int *errp)
{
	struct dfa *dfa;
	struct nfa_set *set, start;
	unsigned long buf[32];

	memset (buf, 0, sizeof (unsigned long) * 32);

	dfa = REGEX_MALLOC (sizeof (struct dfa));
	if (!dfa)
		return NULL;

	vector_head_init (&dfa->states);

	start.size = 1;
	start.head = &nfa->start;
	set = nfa_step (&start, REG_MAGIC, errp);
	if (!set)
		goto err_out_free_dfa;

	dfa->start = dfa_state_alloc (set);
	if (!dfa->start)
		goto err_out_free_set;
	vector_add_tail (&dfa->start->list, &dfa->states);

	if (__dfa_compile (dfa->start, set, &dfa->states) != 0)
		return NULL;

	return dfa;

err_out_free_set:
	REGEX_FREE (set);
err_out_free_dfa:
	REGEX_FREE (dfa);
	return NULL;
}

void
regex_print (struct regex *preg)
{
	REGEX_PRINT ("digraph regex {\n");
	nfa_print (preg->nfa);
	dfa_print (preg->dfa);
	REGEX_PRINT ("}\n");
}

int
regex_compile (struct regex *preg, 
               const char *pattern,
               unsigned int pattern_len,
               int cflags)
{
	int errp = 0;

	memset (preg, 0, sizeof (struct regex));

	preg->nfa = nfa_compile (pattern, pattern_len, 1, cflags, &errp);
	if (!preg->nfa)
		return errp;

//	regex_print (preg);

	preg->dfa = dfa_compile (preg->nfa, &errp);
	if (!preg->dfa)
		return REG_ESPACE;

	return REG_SUCCESS;
}

int
regex_match (const struct regex *preg,
             const char *string,
             unsigned int string_len,
             unsigned int nmatch,
             struct regex_match pmatch[],
             int eflags)
{
	register struct dfa_state *pos = preg->dfa->start;
	register unsigned int i;

	if (pos->final)
		return REG_SUCCESS;

	for (i = 0; i < string_len && pos; i++) {
		pos = pos->table[(unsigned int)string[i]].next;
		if (!pos) {
//            REGEX_PRINT ("terminated at character %u (%u)\n", i, string[i]);
			return REG_NOMATCH;
		}
		else if (pos->final) {
//            REGEX_PRINT ("matched at character %u (%u)\n", i, string[i]);
			return REG_SUCCESS;
		}
	}
	return ((eflags & REG_PARTIAL) ? REG_PARMATCH : REG_NOMATCH);
}

static const char *regex_error_msg[] =
{ "Unknown error",
  "Partial match",
  "No match",
  "Invalid regular expression pattern",
  "Invalid collation character",
  "Invalid character class name",
  "Invalid escape sequence",
  "Invalid back reference",
  "Unbalanced brackets '[' or ']'",
  "Unbalanced paranthesis '(' or ')'",
  "Unbalanced braces '{' or '}'",
  "Invalid content of { }",
  "Invalid range end",
  "Not enough memory space",
  "Invalid repetition operand",
  "Premature end of regular expression",
  "Regular expression too big",
};

int
regex_error (int errcode, char *errbuf, unsigned int errbuf_size)
{
	unsigned int errlen;
	
	if (errcode < REG_SUCCESS || errcode >= REG_ERRCODE_MAX)
		errcode = 0;

	errlen = strlen (regex_error_msg[errcode]);
	if (errlen > errbuf_size)
		errlen = errbuf_size - 1;

	memcpy (errbuf, regex_error_msg[errcode], errlen);
	errbuf[errlen] = '\0';
	return 0;
}

void
regex_free (struct regex *preg)
{

}

