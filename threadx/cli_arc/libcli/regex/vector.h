/*
 *  vector.h
 *
 *  Simple circular doubly linked list library
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
 *  02 Jul 2007: Mohammad Mohsenzadeh <mmohsenz@gmail.com>
 *          - initial implementation
 */

#ifndef __VECTOR_H__
#define __VECTOR_H__

struct vector_node {
	struct vector_node *next, *prev;
};

#define VECTOR_HEAD_INIT(name) \
	{ (struct vector_node *)&(name), (struct vector_node *)&(name) }

#define VECTOR_HEAD(name) \
	struct vector_node name = VECTOR_HEAD_INIT (name)

static inline void
vector_head_init (struct vector_node *head)
{
	head->next = (struct vector_node *)head;
	head->prev = (struct vector_node *)head;
}

static inline void
__vector_add (struct vector_node *first,
              struct vector_node *last,
              struct vector_node *prev,
              struct vector_node *next)
{
	prev->next = first;
	first->prev = prev;
	last->next = next;
	next->prev = last;
}

#define vector_add(new, head) \
	__vector_add (new, new, (struct vector_node *)(head), (head)->next)

#define vector_add_tail(new, head) \
	__vector_add (new, new, (head)->prev, (struct vector_node *)(head))

#define vector_addl(start, end, head) \
	__vector_add (start, end, (struct vector_node *)(head), (head)->next)

#define vector_addl_tail(start, end, head) \
	__vector_add (start, end, (head)->prev, (struct vector_node *)(head))

static inline void
__vector_del (struct vector_node *first,
              struct vector_node *last)
{
	first->prev->next = last->next;
	last->next->prev = first->prev;
	first->prev = NULL;
	last->next = NULL;
}

#define vector_del(entry) __vector_del (entry, entry)

static inline void
__vector_move (struct vector_node *first,
               struct vector_node *last,
               struct vector_node *prev,
               struct vector_node *next)
{
	__vector_del (first, last);
	__vector_add (first, last, prev, next);
}

#define vector_move(entry, head) \
	__vector_move (entry, entry, head, (head)->next)

#define vector_move_tail(entry, head) \
	__vector_move (entry, entry, (head)->prev, head)

#define vector_movel(start, end, head) \
	__vector_move (start, end, head, (head)->next)

#define vector_movel_tail(start, end, head) \
	__vector_move (start, end, (head)->prev, head)

static inline int
vector_empty (const struct vector_node *head)
{
	return (head == head->next);
}

#define container_of(ptr, type, member) \
	(type *)((char *)ptr - ((unsigned int) &((type *)0)->member))

#define vector_entry(ptr, type, member) \
	container_of (ptr, type, member)

#define vector_iterate(pos, head) \
    for (pos = (head)->first; pos != (head); pos = pos->next)

#define vector_iterate_reverse(pos, head) \
    for (pos = (head)->prev; pos != (head); pos = pos->prev)

#define vector_iterate_safe(pos, n, head) \
	for (pos = (head)->next, n = pos->next; \
        pos != (head); pos = n, n = pos->next)

#define vector_iterate_reverse_safe(pos, n, head) \
	for (pos = (head)->prev, n = pos->prev; \
        pos != (head); pos = n, n = pos->prev)

#define vector_iterate_entry(pos, head, member) \
	for (pos = container_of ((head)->next, __typeof__ (*pos), member); \
		&pos->member != (head); \
		pos = container_of (pos->member.next, __typeof__ (*pos), member))

#define vector_iterate_entry_reverse(pos, head, member) \
	for (pos = container_of ((head)->prev, __typeof__ (*pos), member); \
		&pos->member != (head); \
		pos = container_of (pos->member.prev, __typeof__ (*pos), member))

#define vector_iterate_entry_safe(pos, n, head, member) \
	for (pos = container_of ((head)->next, __typeof__ (*pos), member), \
			n = container_of (pos->member.next, __typeof__ (*pos), member); \
		&pos->member != (head); \
		pos = n, n = container_of (pos->member.next, __typeof__ (*pos), member))

#define vector_iterate_entry_reverse_safe(pos, n, head, member) \
	for (pos = container_of ((head)->prev, __typeof__ (*pos), member), \
			n = container_of (pos->member.prev, __typeof__ (*pos), member); \
		&pos->member != (head); \
		pos = n, n = container_of (pos->member.prev, __typeof__ (*pos), member))

#endif /* __VECTOR_H__ */

