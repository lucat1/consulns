package store

import "fmt"

type Key struct {
	Flags     int
	Active    bool
	Published bool
	Content   string
}

func (z Zone) Keys() map[int]Key {
	return z.keys
}

type AddKey struct {
	ID int
	Key
}

func (z *Zone) AddKey(ak AddKey) (err error) {
	if _, found := z.keys[ak.ID]; found {
		err = fmt.Errorf("Zone %s already contains key with id %d", z.domain, ak.ID)
		return
	}

	z.keys[ak.ID] = Key{
		Flags:     ak.Flags,
		Active:    ak.Active,
		Published: ak.Published,
		Content:   ak.Content,
	}
	// TODO: this should be also saved on consul
	return
}

type KeyUpdate struct {
	Active    *bool
	Published *bool
}

func (z *Zone) UpdateKey(id int, upd KeyUpdate) (err error) {
	key, found := z.keys[id]
	if !found {
		err = fmt.Errorf("Zone %s has no key with id %d", z.domain, id)
		return
	}

	if upd.Active != nil {
		key.Active = *upd.Active
	}
	if upd.Published != nil {
		key.Published = *upd.Published
	}
	// TODO: check that the following line is actually necessary
	z.keys[id] = key
	// TODO: this should be also saved on consul
	return
}

func (z *Zone) RemoveKey(id int) (err error) {
	_, found := z.keys[id]
	if !found {
		err = fmt.Errorf("Zone %s has no key with id %d", z.domain, id)
		return
	}

	delete(z.keys, id)
	// TODO: this should be also saved on consul
	return
}
