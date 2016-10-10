
#ifndef _CIRCULAR_BUFFER_H_
#define _CIRCULAR_BUFFER_H_

#define CQ_MAX_ITEMS    1000

#if defined(__THREADX__)

#include   "tx_api.h"

#define GET_LOCK(_mutex_) \
    if ( tx_mutex_get(_mutex_, TX_WAIT_FOREVER) != TX_SUCCESS) {\
      return -1;\
    }\

#define RELEASE_LOCK(_mutex_) \
    if ( tx_mutex_put(_mutex_) != TX_SUCCESS) {\
      return -1;\
    }

#endif  

typedef struct circular_queue_s
{
  int       first;
  int       last;
  int       valid_items;
  char      data[CQ_MAX_ITEMS];
  TX_MUTEX  cq_mutex;
  
} circular_queue_t;

static inline void cq_init(circular_queue_t *this) {

  this->valid_items  =  0;
  this->first       =  0;
  this->last        =  0;
  memset( &this->data, 0 ,CQ_MAX_ITEMS );

  tx_mutex_create(&this->cq_mutex, "cq_mutex", TX_NO_INHERIT);
  
  return;

}

static inline void cq_terminate(circular_queue_t *this) {

  this->valid_items  =  0;
  this->first       =  0;
  this->last        =  0;
  tx_mutex_delete(&this->cq_mutex);
  
  return;

}


static inline int cq_is_empty(circular_queue_t *this) 
{
  return (!(this->valid_items));
}

static inline int cq_add(circular_queue_t *this, char item_val)
{
  if( this->valid_items >= CQ_MAX_ITEMS ) {
    printf("The queue is full\n");
    printf("You cannot add items\n");
    return -1;
  }
  else {
    GET_LOCK(&this->cq_mutex)
    this->valid_items++;
    this->data[this->last] = item_val;
    this->last = (this->last+1)%CQ_MAX_ITEMS;
    RELEASE_LOCK(&this->cq_mutex)

  }
  return 0;
}

static inline int cq_add_str(circular_queue_t *this, char* item_val, int len)
{
  int i = 0;
  if( (this->valid_items + len ) >= CQ_MAX_ITEMS ) {
    printf( "ERROR : Queue is full, Items in queue %d, items to insert %d\n", this->valid_items, len );
    return -1;
  }
  else {
    GET_LOCK(&this->cq_mutex)
      
    for ( i= 0; i < len; i++) {
      this->valid_items++;
      this->data[this->last] = item_val[i];
      this->last = (this->last+1) % CQ_MAX_ITEMS;
    }
    
    RELEASE_LOCK(&this->cq_mutex)
  }
  return 0;
}

static inline int cq_get(circular_queue_t *this, char *item_val)
{
  
  if( cq_is_empty(this) )  {
      // printf("isempty\n");
      return -1;
  }
  else {
    GET_LOCK(&this->cq_mutex)
    *item_val = this->data[this->first];
    this->first = ( (this->first+1) % CQ_MAX_ITEMS);
    this->valid_items--;
    RELEASE_LOCK(&this->cq_mutex)

    return 0;
    
  }

}

static inline void cq_print(circular_queue_t *this)
{
  int first, valid_items;
  first  = this->first;
  valid_items = this->valid_items;
  while( valid_items > 0 ){
    printf("%c", this->data[first] );
    first = ( (first + 1) % CQ_MAX_ITEMS);
    valid_items--;
  }
  printf("\n");

  return;
}


#endif

