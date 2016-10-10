#ifndef _ATLK_QUEUE_H
#define _ATLK_QUEUE_H

#include <atlk/sdk.h>

/**
   @file
   Simple queue implementation
*/

/** Element in queue */
typedef struct queue_elem {
  struct queue_elem *next;
} queue_elem_t;

#define QUEUE_ELEM_INIT { NULL }

/** Queue descriptor */
typedef struct queue {
  queue_elem_t *head;
  queue_elem_t *tail;
} queue_t;

atlk_inline void
queue_init(queue_t *q)
{
  q->head = NULL;
  q->tail = NULL;
}

atlk_inline int
queue_is_empty(const queue_t *q)
{
  return q->head == NULL;
}

atlk_inline int
queue_is_singular(const queue_t *q)
{
  return q->head == q->tail;
}

atlk_inline void
queue_add(queue_elem_t *new_element, queue_t *q)
{
  new_element->next = NULL;

  if (queue_is_empty(q)) {
    q->head = new_element;
  }
  else {
    q->tail->next = new_element;
  }

  q->tail = new_element;
}

atlk_inline void
queue_del(queue_t *q, queue_elem_t **element_ptr)
{
  queue_elem_t *element = NULL;

  if (!queue_is_empty(q)) {
    if (queue_is_singular(q)) {
      q->tail = NULL;
    }
    element = q->head;
    q->head = q->head->next;
    element->next = NULL;
  }

  *element_ptr = element;
}

#endif /* _ATLK_QUEUE_H */
